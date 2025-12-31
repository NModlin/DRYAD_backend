"""
Advanced Caching System for DRYAD.AI Backend
Provides multi-layer caching with Redis, in-memory, and database query optimization.
"""

import asyncio
import hashlib
import json
import os
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, Callable, List
from functools import wraps
from enum import Enum

from app.core.logging_config import get_logger, LogTimer

logger = get_logger(__name__)


class CacheLevel(str, Enum):
    """Cache levels for different storage types."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"


class CacheStrategy(str, Enum):
    """Cache strategies for different use cases."""
    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    LFU = "lfu"  # Least Frequently Used
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


class CacheEntry:
    """Cache entry with metadata."""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 1
        self.ttl = ttl
        self.expires_at = time.time() + ttl if ttl else None
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self):
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


class InMemoryCache:
    """High-performance in-memory cache with multiple eviction strategies."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
    
    def _generate_key(self, key: Union[str, tuple]) -> str:
        """Generate cache key from various input types."""
        if isinstance(key, str):
            return key
        elif isinstance(key, (tuple, list)):
            return hashlib.md5(str(key).encode()).hexdigest()
        else:
            return hashlib.md5(str(key).encode()).hexdigest()
    
    def get(self, key: Union[str, tuple]) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._generate_key(key)
        
        if cache_key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[cache_key]
        
        # Check expiration
        if entry.is_expired():
            del self.cache[cache_key]
            if cache_key in self.access_order:
                self.access_order.remove(cache_key)
            self.stats["misses"] += 1
            self.stats["size"] = len(self.cache)
            return None
        
        # Update access metadata
        entry.touch()
        
        # Update LRU order
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)
        
        self.stats["hits"] += 1
        return entry.value
    
    def set(self, key: Union[str, tuple], value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        # Check if we need to evict
        if len(self.cache) >= self.max_size and cache_key not in self.cache:
            self._evict_lru()
        
        # Store entry
        self.cache[cache_key] = CacheEntry(value, ttl)
        
        # Update access order
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)
        
        self.stats["size"] = len(self.cache)
    
    def delete(self, key: Union[str, tuple]) -> bool:
        """Delete value from cache."""
        cache_key = self._generate_key(key)
        
        if cache_key in self.cache:
            del self.cache[cache_key]
            if cache_key in self.access_order:
                self.access_order.remove(cache_key)
            self.stats["size"] = len(self.cache)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()
        self.stats["size"] = 0
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self.access_order:
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]
                self.stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }


class RedisCache:
    """Redis-based distributed cache."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self.available = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection."""
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            self.available = True
            logger.info("Redis cache initialized successfully")
        except ImportError:
            logger.warning("Redis not installed - distributed caching disabled")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - distributed caching disabled")
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from Redis storage."""
        return pickle.loads(data)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.available:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        if not self.available:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            data = self._serialize(value)
            return self.redis_client.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        if not self.available:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern."""
        if not self.available:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")
            return 0


class MultiLevelCache:
    """Multi-level cache combining memory and Redis."""
    
    def __init__(self, memory_size: int = 1000, redis_url: str = "redis://localhost:6379"):
        self.memory_cache = InMemoryCache(max_size=memory_size)
        self.redis_cache = RedisCache(redis_url=redis_url)
        self.stats = {
            "l1_hits": 0,  # Memory hits
            "l2_hits": 0,  # Redis hits
            "misses": 0,
            "promotions": 0  # Redis -> Memory promotions
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache."""
        # Try L1 (memory) first
        value = self.memory_cache.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value
        
        # Try L2 (Redis)
        value = self.redis_cache.get(key)
        if value is not None:
            self.stats["l2_hits"] += 1
            # Promote to L1
            self.memory_cache.set(key, value)
            self.stats["promotions"] += 1
            return value
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in multi-level cache."""
        # Store in both levels
        self.memory_cache.set(key, value, ttl)
        self.redis_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete from all cache levels."""
        self.memory_cache.delete(key)
        self.redis_cache.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory_cache.get_stats()
        
        total_requests = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["misses"]
        overall_hit_rate = ((self.stats["l1_hits"] + self.stats["l2_hits"]) / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "multi_level": self.stats,
            "memory_cache": memory_stats,
            "redis_available": self.redis_cache.available,
            "overall_hit_rate_percent": round(overall_hit_rate, 2),
            "total_requests": total_requests
        }


# Global cache instance
# Get Redis URL from environment, default to localhost for local development
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
cache = MultiLevelCache(redis_url=redis_url)


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    use_args: bool = True,
    use_kwargs: bool = True
):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            if use_args:
                key_parts.extend(str(arg) for arg in args)
            if use_kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            with LogTimer(f"Function execution: {func.__name__}"):
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            if use_args:
                key_parts.extend(str(arg) for arg in args)
            if use_kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            with LogTimer(f"Function execution: {func.__name__}"):
                result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_clear_pattern(pattern: str) -> int:
    """Clear cache entries matching pattern."""
    # Clear from Redis
    cleared = cache.redis_cache.clear_pattern(pattern)
    
    # Clear from memory (simple implementation)
    memory_cleared = 0
    keys_to_delete = []
    for key in cache.memory_cache.cache.keys():
        if pattern in key:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        cache.memory_cache.delete(key)
        memory_cleared += 1
    
    logger.info(f"Cleared {cleared + memory_cleared} cache entries matching pattern: {pattern}")
    return cleared + memory_cleared


def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive cache statistics."""
    return cache.get_stats()
