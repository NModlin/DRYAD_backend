"""
Archivist Agent - Short-Term Memory Specialist (Level 2)

Manages short-term, episodic memory using Redis with TTL-based expiration.
Part of the Memory Guild cognitive architecture.

Responsibilities:
- Store/retrieve recent context in Redis
- TTL-based automatic expiration
- Key-value and hash operations
- Memory prioritization
- Automatic archival triggers
"""

import json
import asyncio
from datetime import timedelta, datetime, timezone
from typing import Any, Dict, Optional, List
from uuid import uuid4, UUID

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from pydantic import BaseModel, Field
from dryad.services.logging.logger import StructuredLogger

logger = StructuredLogger("archivist")


class MemoryEntry(BaseModel):
    """Short-term memory entry."""
    entry_id: UUID = Field(default_factory=uuid4)
    key: str
    value: Dict[str, Any]
    ttl_seconds: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime


class ArchivistAgent:
    """
    Level 2 Component: Archivist Agent
    
    Manages short-term memory (Redis) with automatic expiration.
    Handles recent context, active workflows, and temporary data.
    """
    
    DEFAULT_TTL = timedelta(hours=24)
    MAX_TTL = timedelta(days=7)
    
    def __init__(self, redis_url: str = "redis://localhost:6379", mock_mode: bool = None):
        """
        Initialize Archivist Agent.
        
        Args:
            redis_url: Redis connection URL
            mock_mode: Force mock mode (None = auto-detect)
        """
        self.redis_url = redis_url
        
        # Determine if we should use mock mode
        if mock_mode is None:
            self.mock_mode = not REDIS_AVAILABLE or not self._check_redis_available()
        else:
            self.mock_mode = mock_mode
        
        if self.mock_mode:
            logger.log_warning("archivist_init", {"mode": "mock", "reason": "Redis unavailable"})
            self.redis_client = None
            self.mock_storage: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        else:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.log_info("archivist_init", {"mode": "redis", "url": redis_url})
    
    def _check_redis_available(self) -> bool:
        """Check if Redis is available."""
        if not REDIS_AVAILABLE:
            return False

        try:
            # Try to create a client and ping with very short timeout
            import redis as sync_redis
            client = sync_redis.from_url(
                self.redis_url,
                socket_connect_timeout=0.1,  # Very short timeout
                socket_timeout=0.1
            )
            result = client.ping()
            client.close()
            if not result:
                logger.log_warning("redis_check", {"available": False, "reason": "ping failed"})
                return False
            return True
        except Exception as e:
            logger.log_warning("redis_check", {"available": False, "error": str(e)})
            return False
    
    async def store(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[timedelta] = None,
        tenant_id: str = "default",
        agent_id: str = "system"
    ) -> bool:
        """
        Store value in short-term memory.
        
        Args:
            key: Memory key
            value: Memory value (dict)
            ttl: Time-to-live (default: 24 hours)
            tenant_id: Tenant identifier for multi-tenancy
            agent_id: Agent identifier
            
        Returns:
            True if successful, False otherwise
        """
        ttl = ttl or self.DEFAULT_TTL
        
        # Enforce max TTL
        if ttl > self.MAX_TTL:
            ttl = self.MAX_TTL
        
        # Create namespaced key
        namespaced_key = f"{tenant_id}:{agent_id}:{key}"
        
        try:
            if self.mock_mode:
                # Mock implementation
                expiry_time = datetime.now(timezone.utc) + ttl
                self.mock_storage[namespaced_key] = (value, expiry_time)
                
                logger.log_info(
                    "memory_stored",
                    {
                        "key": namespaced_key,
                        "ttl_seconds": int(ttl.total_seconds()),
                        "mode": "mock"
                    }
                )
                return True
            else:
                # Redis implementation
                await self.redis_client.setex(
                    namespaced_key,
                    int(ttl.total_seconds()),
                    json.dumps(value)
                )
                
                logger.log_info(
                    "memory_stored",
                    {
                        "key": namespaced_key,
                        "ttl_seconds": int(ttl.total_seconds()),
                        "mode": "redis"
                    }
                )
                return True
                
        except Exception as e:
            logger.log_error("store_failed", {"key": namespaced_key, "error": str(e)})
            return False
    
    async def retrieve(
        self,
        key: str,
        tenant_id: str = "default",
        agent_id: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve value from short-term memory.
        
        Args:
            key: Memory key
            tenant_id: Tenant identifier
            agent_id: Agent identifier
            
        Returns:
            Memory value if found and not expired, None otherwise
        """
        namespaced_key = f"{tenant_id}:{agent_id}:{key}"
        
        try:
            if self.mock_mode:
                # Mock implementation
                if namespaced_key in self.mock_storage:
                    value, expiry_time = self.mock_storage[namespaced_key]

                    # Check if expired
                    if datetime.now(timezone.utc) > expiry_time:
                        del self.mock_storage[namespaced_key]
                        logger.log_info("memory_expired", {"key": namespaced_key, "mode": "mock"})
                        return None
                    
                    logger.log_info("memory_retrieved", {"key": namespaced_key, "mode": "mock"})
                    return value
                else:
                    logger.log_info("memory_not_found", {"key": namespaced_key, "mode": "mock"})
                    return None
            else:
                # Redis implementation
                value = await self.redis_client.get(namespaced_key)
                
                if value is None:
                    logger.log_info("memory_not_found", {"key": namespaced_key, "mode": "redis"})
                    return None
                
                logger.log_info("memory_retrieved", {"key": namespaced_key, "mode": "redis"})
                return json.loads(value)
                
        except Exception as e:
            logger.log_error("retrieve_failed", {"key": namespaced_key, "error": str(e)})
            return None
    
    async def delete(
        self,
        key: str,
        tenant_id: str = "default",
        agent_id: str = "system"
    ) -> bool:
        """
        Delete value from short-term memory.
        
        Args:
            key: Memory key
            tenant_id: Tenant identifier
            agent_id: Agent identifier
            
        Returns:
            True if successful, False otherwise
        """
        namespaced_key = f"{tenant_id}:{agent_id}:{key}"
        
        try:
            if self.mock_mode:
                # Mock implementation
                if namespaced_key in self.mock_storage:
                    del self.mock_storage[namespaced_key]
                    logger.log_info("memory_deleted", {"key": namespaced_key, "mode": "mock"})
                    return True
                else:
                    logger.log_info("memory_not_found", {"key": namespaced_key, "mode": "mock"})
                    return False
            else:
                # Redis implementation
                result = await self.redis_client.delete(namespaced_key)
                logger.log_info("memory_deleted", {"key": namespaced_key, "deleted": result > 0, "mode": "redis"})
                return result > 0
                
        except Exception as e:
            logger.log_error("delete_failed", {"key": namespaced_key, "error": str(e)})
            return False
    
    async def list_keys(
        self,
        pattern: str = "*",
        tenant_id: str = "default",
        agent_id: str = "system"
    ) -> List[str]:
        """
        List keys matching pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            tenant_id: Tenant identifier
            agent_id: Agent identifier
            
        Returns:
            List of matching keys (without namespace prefix)
        """
        namespaced_pattern = f"{tenant_id}:{agent_id}:{pattern}"
        prefix = f"{tenant_id}:{agent_id}:"
        
        try:
            if self.mock_mode:
                # Mock implementation
                import fnmatch
                matching_keys = [
                    key.replace(prefix, "")
                    for key in self.mock_storage.keys()
                    if fnmatch.fnmatch(key, namespaced_pattern)
                ]
                return matching_keys
            else:
                # Redis implementation
                keys = await self.redis_client.keys(namespaced_pattern)
                return [key.replace(prefix, "") for key in keys]
                
        except Exception as e:
            logger.log_error("list_keys_failed", {"pattern": namespaced_pattern, "error": str(e)})
            return []
    
    async def cleanup_expired(self) -> int:
        """
        Cleanup expired entries (mock mode only, Redis handles this automatically).
        
        Returns:
            Number of entries cleaned up
        """
        if not self.mock_mode:
            return 0

        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, (_, expiry) in self.mock_storage.items()
            if now > expiry
        ]
        
        for key in expired_keys:
            del self.mock_storage[key]
        
        if expired_keys:
            logger.log_info("cleanup_expired", {"count": len(expired_keys)})
        
        return len(expired_keys)
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client and not self.mock_mode:
            await self.redis_client.close()
            logger.log_info("archivist_closed", {})

