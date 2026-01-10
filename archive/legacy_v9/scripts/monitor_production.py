"""
Production Monitoring Dashboard
DRYAD.AI Agent Evolution Architecture

Real-time monitoring dashboard that displays system metrics,
health status, and performance statistics.
"""

import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class ProductionMonitor:
    """Real-time production monitoring dashboard."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize monitor."""
        self.api_url = api_url
        self.running = True
    
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def fetch_health(self) -> Dict[str, Any]:
        """Fetch health status."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.json() if response.status_code == 200 else {"status": "error"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    def fetch_metrics(self) -> Dict[str, Any]:
        """Fetch metrics."""
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=2)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            return {}
    
    def fetch_system_status(self) -> Dict[str, Any]:
        """Fetch system status."""
        try:
            response = requests.get(f"{self.api_url}/api/v1/system/status", timeout=2)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            return {}
    
    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        elif seconds < 86400:
            return f"{seconds/3600:.1f}h"
        else:
            return f"{seconds/86400:.1f}d"
    
    def display_header(self):
        """Display dashboard header."""
        print("="*80)
        print("DRYAD.AI PRODUCTION MONITORING DASHBOARD".center(80))
        print("="*80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        print(f"API: {self.api_url}".center(80))
        print("="*80)
    
    def display_health(self, health: Dict[str, Any]):
        """Display health status."""
        print("\n📊 SYSTEM HEALTH")
        print("-" * 80)
        
        status = health.get("status", "unknown")
        if status == "healthy":
            print(f"  Status: ✅ {status.upper()}")
        elif status == "unreachable":
            print(f"  Status: ❌ {status.upper()}")
            print(f"  Error: {health.get('error', 'Unknown')}")
        else:
            print(f"  Status: ⚠️  {status.upper()}")
    
    def display_system_status(self, status: Dict[str, Any]):
        """Display system status."""
        if not status:
            return
        
        print("\n🔧 SYSTEM STATUS")
        print("-" * 80)
        
        print(f"  Status: {status.get('status', 'unknown')}")
        
        uptime = status.get('uptime_seconds', 0)
        print(f"  Uptime: {self.format_uptime(uptime)}")
        
        # Level status
        levels = status.get('levels', {})
        if levels:
            print("\n  Architecture Levels:")
            for level, level_status in levels.items():
                icon = "✅" if level_status == "operational" else "❌"
                print(f"    {icon} {level}: {level_status}")
    
    def display_metrics(self, metrics: Dict[str, Any]):
        """Display metrics."""
        if not metrics:
            return
        
        print("\n📈 PERFORMANCE METRICS")
        print("-" * 80)
        
        # Uptime
        uptime = metrics.get('uptime_seconds', 0)
        print(f"  Uptime: {self.format_uptime(uptime)}")
        
        # Counters
        counters = metrics.get('counters', {})
        if counters:
            print("\n  Counters:")
            
            # Code review metrics
            code_review_metrics = {k: v for k, v in counters.items() if 'code_review' in k}
            if code_review_metrics:
                print("    Code Reviews:")
                for key, value in sorted(code_review_metrics.items()):
                    # Clean up key for display
                    display_key = key.split('{')[0].replace('code_review_', '').replace('_', ' ').title()
                    print(f"      {display_key}: {value}")
        
        # Timings
        timings = metrics.get('timings', {})
        if timings:
            print("\n  Timings:")
            for key, stats in timings.items():
                display_key = key.split('{')[0].replace('_', ' ').title()
                print(f"    {display_key}:")
                print(f"      Count: {stats.get('count', 0)}")
                print(f"      Mean: {stats.get('mean', 0):.3f}s")
                print(f"      P50: {stats.get('p50', 0):.3f}s")
                print(f"      P95: {stats.get('p95', 0):.3f}s")
                print(f"      P99: {stats.get('p99', 0):.3f}s")
    
    def display_code_review_stats(self, status: Dict[str, Any]):
        """Display code review statistics."""
        metrics = status.get('metrics', {})
        if not metrics:
            return
        
        print("\n🔍 CODE REVIEW STATISTICS")
        print("-" * 80)
        
        total = metrics.get('code_reviews_total', 0)
        completed = metrics.get('code_reviews_completed', 0)
        escalated = metrics.get('code_reviews_escalated', 0)
        
        print(f"  Total Reviews: {total}")
        print(f"  Completed: {completed}")
        print(f"  Escalated: {escalated}")
        
        if total > 0:
            completion_rate = (completed / total) * 100
            escalation_rate = (escalated / total) * 100
            print(f"\n  Completion Rate: {completion_rate:.1f}%")
            print(f"  Escalation Rate: {escalation_rate:.1f}%")
    
    def display_footer(self):
        """Display dashboard footer."""
        print("\n" + "="*80)
        print("Press Ctrl+C to exit | Refreshing every 5 seconds...".center(80))
        print("="*80)
    
    def run(self):
        """Run monitoring dashboard."""
        print("\n🚀 Starting Production Monitor...")
        print("Connecting to API server...\n")
        time.sleep(1)
        
        try:
            while self.running:
                # Clear screen
                self.clear_screen()
                
                # Fetch data
                health = self.fetch_health()
                metrics = self.fetch_metrics()
                status = self.fetch_system_status()
                
                # Display dashboard
                self.display_header()
                self.display_health(health)
                self.display_system_status(status)
                self.display_metrics(metrics)
                self.display_code_review_stats(status)
                self.display_footer()
                
                # Wait before refresh
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitor stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n\n❌ Monitor error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DRYAD.AI Production Monitor")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API server URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    monitor = ProductionMonitor(api_url=args.url)
    monitor.run()


if __name__ == "__main__":
    main()

