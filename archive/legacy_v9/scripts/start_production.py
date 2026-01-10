"""
Production Server Startup Script
DRYAD.AI Agent Evolution Architecture

Starts the production API server with proper configuration,
health checks, and monitoring.
"""

import os
import sys
import time
import asyncio
import uvicorn
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.database import SessionLocal
from app.services.logging.logger import StructuredLogger


logger = StructuredLogger("production_startup")


def check_database():
    """Check database connectivity."""
    print("\n[1/5] Checking database connectivity...")
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("  ✅ Database connection successful")
        return True
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False


def check_redis():
    """Check Redis connectivity (optional)."""
    print("\n[2/5] Checking Redis connectivity...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
        r.ping()
        print("  ✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"  ⚠️  Redis connection failed (optional): {e}")
        print("  ℹ️  System will use mock storage for Archivist")
        return False


def check_chromadb():
    """Check ChromaDB connectivity (optional)."""
    print("\n[3/5] Checking ChromaDB connectivity...")
    try:
        import chromadb
        client = chromadb.Client()
        print("  ✅ ChromaDB connection successful")
        return True
    except Exception as e:
        print(f"  ⚠️  ChromaDB connection failed (optional): {e}")
        print("  ℹ️  System will use mock storage for Librarian")
        return False


def check_ollama():
    """Check Ollama connectivity (optional)."""
    print("\n[4/5] Checking Ollama connectivity...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("  ✅ Ollama connection successful")
            return True
        else:
            print(f"  ⚠️  Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️  Ollama connection failed (optional): {e}")
        print("  ℹ️  System will use mock LLM responses")
        return False


def display_startup_banner():
    """Display startup banner."""
    print("\n" + "="*70)
    print("DRYAD.AI AGENT EVOLUTION ARCHITECTURE")
    print("Production API Server")
    print("="*70)
    print("\nVersion: 1.0.0")
    print("Environment: Production")
    print("Date:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("\nArchitecture Levels:")
    print("  ✅ Level 0: Foundation Services")
    print("  ✅ Level 1: Execution & Memory Agents")
    print("  ✅ Level 2: Stateful Operations")
    print("  ✅ Level 3: Orchestration & HITL")
    print("  ✅ Level 4: Evaluation Framework")
    print("  ✅ Level 5: Self-Improvement")
    print("\n" + "="*70)


def run_health_checks():
    """Run all health checks."""
    print("\n🔍 Running Health Checks...")
    print("="*70)
    
    results = {
        "database": check_database(),
        "redis": check_redis(),
        "chromadb": check_chromadb(),
        "ollama": check_ollama()
    }
    
    print("\n[5/5] Health Check Summary")
    print("="*70)
    
    critical_ok = results["database"]
    optional_count = sum([results["redis"], results["chromadb"], results["ollama"]])
    
    if critical_ok:
        print(f"  ✅ Critical services: OK")
        print(f"  ℹ️  Optional services: {optional_count}/3 available")
        print("\n  System is ready to start!")
        return True
    else:
        print(f"  ❌ Critical services: FAILED")
        print("\n  Cannot start server. Fix database connection first.")
        return False


def start_server():
    """Start the production server."""
    print("\n🚀 Starting Production Server...")
    print("="*70)
    print("\nServer Configuration:")
    print("  Host: 0.0.0.0")
    print("  Port: 8000")
    print("  Workers: 1 (development mode)")
    print("  Reload: False")
    print("\nEndpoints:")
    print("  API Root:       http://localhost:8000/")
    print("  Health Check:   http://localhost:8000/health")
    print("  Metrics (JSON): http://localhost:8000/metrics")
    print("  Metrics (Prom): http://localhost:8000/metrics/prometheus")
    print("  Code Review:    http://localhost:8000/api/v1/code-review")
    print("  System Status:  http://localhost:8000/api/v1/system/status")
    print("\n" + "="*70)
    print("\n🎉 Server is starting... Press Ctrl+C to stop\n")
    
    # Start uvicorn server
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True
    )


def main():
    """Main entry point."""
    try:
        # Display banner
        display_startup_banner()
        
        # Run health checks
        if not run_health_checks():
            sys.exit(1)
        
        # Start server
        start_server()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

