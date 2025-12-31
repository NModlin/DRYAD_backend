"""
Benchmark Registry
DRYAD.AI Agent Evolution Architecture - Level 4

Manages standardized evaluation benchmarks with versioning support.
Provides registration, retrieval, and lifecycle management of benchmarks.
"""

import sqlite3
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("dryad.benchmark_registry")


class BenchmarkCreate(BaseModel):
    """Schema for creating a new benchmark."""
    name: str
    version: str
    description: Optional[str] = None
    category: str = Field(..., pattern="^(reasoning|tool_use|memory|collaboration|general)$")
    dataset_uri: str
    evaluation_logic_uri: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Benchmark(BaseModel):
    """Schema for benchmark response."""
    benchmark_id: str
    name: str
    version: str
    description: Optional[str]
    category: str
    dataset_uri: str
    evaluation_logic_uri: str
    metadata: Dict[str, Any]
    created_at: str
    is_active: bool


class BenchmarkRegistry:
    """
    Level 4 Component: Benchmark Registry
    
    Manages standardized evaluation benchmarks with versioning.
    Ensures benchmark uniqueness and provides retrieval capabilities.
    """
    
    def __init__(self, db: Session):
        self.db = db
        logger.log_info("benchmark_registry_initialized", {})
    
    def register_benchmark(
        self,
        benchmark: BenchmarkCreate,
        tenant_id: str = "default"
    ) -> Benchmark:
        """
        Register a new benchmark.
        
        Args:
            benchmark: Benchmark creation data
            tenant_id: Tenant identifier for multi-tenancy
            
        Returns:
            Created benchmark
            
        Raises:
            ValueError: If benchmark with same name/version exists
        """
        try:
            # Generate benchmark ID
            benchmark_id = f"bench_{uuid.uuid4().hex[:12]}"
            
            # Get raw connection for direct SQL
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            # Check if benchmark with same name/version exists
            cursor.execute(
                "SELECT benchmark_id FROM benchmarks WHERE name = ? AND version = ?",
                (benchmark.name, benchmark.version)
            )
            existing = cursor.fetchone()
            
            if existing:
                raise ValueError(f"Benchmark {benchmark.name} v{benchmark.version} already exists")
            
            # Insert benchmark
            cursor.execute("""
                INSERT INTO benchmarks (
                    benchmark_id, name, version, description, category,
                    dataset_uri, evaluation_logic_uri, metadata, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                benchmark_id,
                benchmark.name,
                benchmark.version,
                benchmark.description,
                benchmark.category,
                benchmark.dataset_uri,
                benchmark.evaluation_logic_uri,
                json.dumps(benchmark.metadata),
                datetime.now().isoformat(),
                1  # is_active = True
            ))
            
            connection.commit()
            
            logger.log_info(
                "benchmark_registered",
                {
                    "benchmark_id": benchmark_id,
                    "name": benchmark.name,
                    "version": benchmark.version,
                    "category": benchmark.category
                }
            )
            
            return Benchmark(
                benchmark_id=benchmark_id,
                name=benchmark.name,
                version=benchmark.version,
                description=benchmark.description,
                category=benchmark.category,
                dataset_uri=benchmark.dataset_uri,
                evaluation_logic_uri=benchmark.evaluation_logic_uri,
                metadata=benchmark.metadata,
                created_at=datetime.now().isoformat(),
                is_active=True
            )
            
        except Exception as e:
            logger.log_error("benchmark_registration_failed", {"error": str(e)})
            raise
    
    def get_benchmark(
        self,
        benchmark_id: str
    ) -> Optional[Benchmark]:
        """
        Retrieve a benchmark by ID.
        
        Args:
            benchmark_id: Benchmark identifier
            
        Returns:
            Benchmark if found, None otherwise
        """
        try:
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT benchmark_id, name, version, description, category,
                       dataset_uri, evaluation_logic_uri, metadata, created_at, is_active
                FROM benchmarks
                WHERE benchmark_id = ?
            """, (benchmark_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return Benchmark(
                benchmark_id=row[0],
                name=row[1],
                version=row[2],
                description=row[3],
                category=row[4],
                dataset_uri=row[5],
                evaluation_logic_uri=row[6],
                metadata=json.loads(row[7]) if row[7] else {},
                created_at=row[8],
                is_active=bool(row[9])
            )
            
        except Exception as e:
            logger.log_error("benchmark_retrieval_failed", {"error": str(e)})
            return None
    
    def list_benchmarks(
        self,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[Benchmark]:
        """
        List all benchmarks with optional filtering.
        
        Args:
            category: Filter by category
            active_only: Only return active benchmarks
            
        Returns:
            List of benchmarks
        """
        try:
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            query = """
                SELECT benchmark_id, name, version, description, category,
                       dataset_uri, evaluation_logic_uri, metadata, created_at, is_active
                FROM benchmarks
                WHERE 1=1
            """
            params = []
            
            if active_only:
                query += " AND is_active = ?"
                params.append(1)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            benchmarks = []
            for row in rows:
                benchmarks.append(Benchmark(
                    benchmark_id=row[0],
                    name=row[1],
                    version=row[2],
                    description=row[3],
                    category=row[4],
                    dataset_uri=row[5],
                    evaluation_logic_uri=row[6],
                    metadata=json.loads(row[7]) if row[7] else {},
                    created_at=row[8],
                    is_active=bool(row[9])
                ))
            
            logger.log_info("benchmarks_listed", {"count": len(benchmarks), "category": category})
            
            return benchmarks
            
        except Exception as e:
            logger.log_error("benchmark_listing_failed", {"error": str(e)})
            return []
    
    def deactivate_benchmark(
        self,
        benchmark_id: str
    ) -> bool:
        """
        Deactivate a benchmark (soft delete).
        
        Args:
            benchmark_id: Benchmark identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE benchmarks SET is_active = 0 WHERE benchmark_id = ?",
                (benchmark_id,)
            )
            
            connection.commit()
            
            logger.log_info("benchmark_deactivated", {"benchmark_id": benchmark_id})
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.log_error("benchmark_deactivation_failed", {"error": str(e)})
            return False

