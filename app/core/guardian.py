"""
Guardian Agent - Log Monitoring and Error Detection
Part of the Self-Healing System using Governed Agentic Development (GAD)

The Guardian continuously monitors error logs and initiates the self-healing workflow
when critical errors are detected.
"""

import asyncio
import re
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
import httpx

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ErrorPattern:
    """Represents a detected error pattern."""
    
    def __init__(self, error_type: str, error_message: str, file_path: str, 
                 line_number: int, stack_trace: str, full_log: str):
        self.error_type = error_type
        self.error_message = error_message
        self.file_path = file_path
        self.line_number = line_number
        self.stack_trace = stack_trace
        self.full_log = full_log
        self.timestamp = datetime.now()
        self.severity = self._classify_severity()
        self.hash = self._compute_hash()
    
    def _classify_severity(self) -> str:
        """Classify error severity based on type and context."""
        critical_errors = [
            "DatabaseError", "ConnectionError", "MemoryError",
            "SystemExit", "KeyboardInterrupt"
        ]
        
        high_errors = [
            "KeyError", "AttributeError", "TypeError", "ValueError",
            "IndexError", "ImportError", "ModuleNotFoundError"
        ]
        
        if self.error_type in critical_errors:
            return "critical"
        elif self.error_type in high_errors:
            return "high"
        elif "Warning" in self.error_type:
            return "low"
        else:
            return "medium"
    
    def _compute_hash(self) -> str:
        """Compute unique hash for deduplication."""
        content = f"{self.error_type}:{self.file_path}:{self.line_number}:{self.error_message}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API submission."""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "stack_trace": self.stack_trace,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "hash": self.hash
        }


class Guardian:
    """
    Guardian Agent - Monitors logs and detects errors.
    
    Responsibilities:
    - Tail error log file in real-time
    - Parse and extract error information
    - Classify error severity
    - Deduplicate errors
    - Submit to orchestrator for healing
    """
    
    def __init__(self, 
                 log_path: str = "logs/gremlins_errors.log",
                 orchestrator_url: str = "http://localhost:8000",
                 check_interval: float = 2.0,
                 dedup_window: int = 300):
        """
        Initialize Guardian.
        
        Args:
            log_path: Path to error log file
            orchestrator_url: Base URL of orchestrator API
            check_interval: Seconds between log checks
            dedup_window: Seconds to remember errors for deduplication
        """
        self.log_path = Path(log_path)
        self.orchestrator_url = orchestrator_url
        self.check_interval = check_interval
        self.dedup_window = dedup_window
        
        # Deduplication tracking
        self.seen_errors: deque = deque(maxlen=1000)
        self.error_timestamps: Dict[str, datetime] = {}
        
        # Statistics
        self.errors_detected = 0
        self.errors_submitted = 0
        self.errors_deduplicated = 0
        
        self.running = False
        self.last_position = 0
    
    async def start(self):
        """Start the Guardian monitoring service."""
        logger.info("Guardian Agent starting...")
        
        # Ensure log file exists
        if not self.log_path.exists():
            logger.warning(f"Log file not found: {self.log_path}")
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.touch()
        
        # Get initial file position (start from end)
        self.last_position = self.log_path.stat().st_size
        
        self.running = True
        logger.info(f"Guardian monitoring: {self.log_path}")
        
        try:
            await self._monitor_loop()
        except Exception as e:
            logger.error(f"Guardian error: {e}", exc_info=True)
            self.running = False
    
    async def stop(self):
        """Stop the Guardian monitoring service."""
        logger.info("🛡️ Guardian Agent stopping...")
        self.running = False
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Check for new log entries
                new_lines = await self._read_new_lines()
                
                if new_lines:
                    # Parse errors from new lines
                    errors = self._parse_errors(new_lines)
                    
                    # Process each error
                    for error in errors:
                        await self._process_error(error)
                
                # Clean up old deduplication entries
                self._cleanup_dedup_cache()
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def _read_new_lines(self) -> List[str]:
        """Read new lines from log file since last check."""
        try:
            current_size = self.log_path.stat().st_size
            
            # Check if file was truncated
            if current_size < self.last_position:
                logger.warning("Log file was truncated, resetting position")
                self.last_position = 0
            
            # No new content
            if current_size == self.last_position:
                return []
            
            # Read new content
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()
            
            return new_content.strip().split('\n') if new_content.strip() else []
            
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return []
    
    def _parse_errors(self, lines: List[str]) -> List[ErrorPattern]:
        """Parse error patterns from log lines."""
        errors = []
        current_error = None
        stack_lines = []
        
        # Regex patterns for error detection
        error_pattern = re.compile(
            r'"level":\s*"ERROR".*?"message":\s*"([^"]+)".*?"module":\s*"([^"]+)".*?"line":\s*(\d+)'
        )
        
        traceback_pattern = re.compile(r'Traceback \(most recent call last\):')
        exception_pattern = re.compile(r'^(\w+Error|\w+Exception):\s*(.+)$')
        file_line_pattern = re.compile(r'File "([^"]+)", line (\d+)')
        
        for line in lines:
            # Check for JSON error log
            error_match = error_pattern.search(line)
            if error_match:
                message, module, line_num = error_match.groups()
                
                # Try to extract more details
                error_type = "UnknownError"
                file_path = f"app/{module.replace('.', '/')}.py"
                
                # Look for exception type in message
                exc_match = re.search(r'(\w+Error|\w+Exception)', message)
                if exc_match:
                    error_type = exc_match.group(1)
                
                error = ErrorPattern(
                    error_type=error_type,
                    error_message=message,
                    file_path=file_path,
                    line_number=int(line_num),
                    stack_trace=line,
                    full_log=line
                )
                errors.append(error)
                self.errors_detected += 1
        
        return errors
    
    async def _process_error(self, error: ErrorPattern):
        """Process a detected error."""
        # Check if we should skip this error
        if not self._should_process(error):
            self.errors_deduplicated += 1
            return
        
        # Record this error
        self.seen_errors.append(error.hash)
        self.error_timestamps[error.hash] = error.timestamp
        
        logger.warning(
            f"Guardian detected error: {error.error_type} in {error.file_path}:{error.line_number}"
        )
        
        # Submit to orchestrator
        await self._submit_to_orchestrator(error)
    
    def _should_process(self, error: ErrorPattern) -> bool:
        """Check if error should be processed (deduplication)."""
        # Skip low severity errors
        if error.severity == "low":
            return False
        
        # Check if we've seen this error recently
        if error.hash in self.error_timestamps:
            last_seen = self.error_timestamps[error.hash]
            time_diff = (error.timestamp - last_seen).total_seconds()
            
            # Skip if seen within dedup window
            if time_diff < self.dedup_window:
                return False
        
        return True
    
    def _cleanup_dedup_cache(self):
        """Remove old entries from deduplication cache."""
        cutoff = datetime.now() - timedelta(seconds=self.dedup_window)
        
        # Remove old timestamps
        to_remove = [
            hash_val for hash_val, timestamp in self.error_timestamps.items()
            if timestamp < cutoff
        ]
        
        for hash_val in to_remove:
            del self.error_timestamps[hash_val]
    
    async def _submit_to_orchestrator(self, error: ErrorPattern):
        """Submit error to orchestrator for self-healing."""
        try:
            url = f"{self.orchestrator_url}/api/v1/orchestrator/self-healing/"
            
            # Generate goal description
            goal = self._generate_goal(error)
            
            payload = {
                "task_type": "self_healing_fix",
                "error_details": error.to_dict(),
                "goal": goal,
                "timestamp": error.timestamp.isoformat()
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    self.errors_submitted += 1
                    task_id = response.json().get("task_id")
                    logger.info(f"✅ Error submitted to orchestrator: {task_id}")
                else:
                    logger.error(f"Failed to submit error: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error submitting to orchestrator: {e}", exc_info=True)
    
    def _generate_goal(self, error: ErrorPattern) -> str:
        """Generate a goal description for the error."""
        return (
            f"Fix {error.error_type} in {error.file_path} at line {error.line_number}. "
            f"Error message: {error.error_message}. "
            f"Add proper error handling and validation to prevent this error."
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Guardian statistics."""
        return {
            "running": self.running,
            "errors_detected": self.errors_detected,
            "errors_submitted": self.errors_submitted,
            "errors_deduplicated": self.errors_deduplicated,
            "active_dedup_entries": len(self.error_timestamps)
        }


# Global Guardian instance (lazy initialization)
_guardian = None


def _get_guardian() -> Guardian:
    """Get or create the global Guardian instance."""
    global _guardian
    if _guardian is None:
        _guardian = Guardian()
    return _guardian


async def start_guardian():
    """Start the Guardian service."""
    guardian = _get_guardian()
    await guardian.start()


async def stop_guardian():
    """Stop the Guardian service."""
    guardian = _get_guardian()
    await guardian.stop()


def get_guardian_stats() -> Dict[str, Any]:
    """Get Guardian statistics."""
    guardian = _get_guardian()
    return guardian.get_stats()

