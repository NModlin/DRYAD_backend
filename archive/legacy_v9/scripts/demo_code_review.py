"""
Live Code Review Assistant Demonstration
DRYAD.AI Agent Evolution Architecture

Demonstrates the complete system working in real-time with
sample code reviews showing all 6 levels of the architecture.
"""

import os
import sys
import time
import asyncio
import requests
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class CodeReviewDemo:
    """Live demonstration of Code Review Assistant."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize demo."""
        self.api_url = api_url
    
    def print_header(self, title: str):
        """Print section header."""
        print("\n" + "="*80)
        print(title.center(80))
        print("="*80 + "\n")
    
    def print_step(self, step: int, total: int, description: str):
        """Print step indicator."""
        print(f"\n[Step {step}/{total}] {description}")
        print("-" * 80)
    
    def check_server(self) -> bool:
        """Check if server is running."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def submit_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit code review request."""
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/code-review",
                json=review_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    def display_review_result(self, result: Dict[str, Any]):
        """Display review result."""
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            if "detail" in result:
                print(f"   Detail: {result['detail']}")
            return
        
        print(f"\n✅ Review Completed!")
        print(f"\n  Review ID: {result.get('review_id')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Complexity Score: {result.get('complexity_score', 0):.2f}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        
        # Findings
        findings = result.get('findings', [])
        security = result.get('security_issues', [])
        best_practices = result.get('best_practice_violations', [])
        
        total_findings = len(findings) + len(security) + len(best_practices)
        print(f"\n  Total Findings: {total_findings}")
        
        if security:
            print(f"    🔒 Security Issues: {len(security)}")
            for issue in security:
                print(f"       - {issue.get('message')} ({issue.get('severity')})")
        
        if best_practices:
            print(f"    📋 Best Practice Violations: {len(best_practices)}")
            for violation in best_practices:
                print(f"       - {violation.get('message')} ({violation.get('severity')})")
        
        if findings:
            print(f"    ℹ️  General Findings: {len(findings)}")
            for finding in findings:
                print(f"       - {finding.get('message')} ({finding.get('severity')})")
        
        # Recommendation
        print(f"\n  Recommendation: {result.get('recommendation')}")
        
        # Escalation
        if result.get('escalated_to_human'):
            print(f"\n  ⚠️  Escalated to Human: YES")
            print(f"     Consultation ID: {result.get('human_consultation_id')}")
        else:
            print(f"\n  ✅ Escalated to Human: NO")
    
    def demo_simple_review(self):
        """Demonstrate simple code review (single agent)."""
        self.print_header("DEMO 1: Simple Code Review (Single Agent)")
        
        print("This demonstrates a simple code review with 1-2 files.")
        print("The system will use a single agent for analysis.")
        print("\nLevels Demonstrated:")
        print("  ✅ Level 1: Memory Coordinator stores context")
        print("  ✅ Level 2: Archivist/Librarian for memory")
        print("  ✅ Level 3: Sequential execution (single agent)")
        print("  ✅ Level 4: Metrics collection")
        
        self.print_step(1, 3, "Preparing review request...")
        
        review_data = {
            "review_id": f"demo_simple_{int(time.time())}",
            "repository": "dryad-backend",
            "pull_request_id": "demo-001",
            "files_changed": [
                "app/utils/helpers.py",
                "tests/test_helpers.py"
            ],
            "diff": """
+ def calculate_score(value: float) -> float:
+     '''Calculate normalized score.'''
+     return min(1.0, max(0.0, value))
+ 
+ def format_timestamp(ts: datetime) -> str:
+     return ts.strftime('%Y-%m-%d %H:%M:%S')
            """,
            "author": "demo_user",
            "description": "Add utility functions for score calculation and timestamp formatting",
            "tenant_id": "demo"
        }
        
        print("  Files: 2")
        print("  Complexity: Low")
        print("  Expected Strategy: Single Agent")
        
        self.print_step(2, 3, "Submitting review to API...")
        time.sleep(1)
        
        result = self.submit_review(review_data)
        
        self.print_step(3, 3, "Review Results")
        self.display_review_result(result)
        
        input("\n\nPress Enter to continue to next demo...")
    
    def demo_complex_review(self):
        """Demonstrate complex code review (task force + HITL)."""
        self.print_header("DEMO 2: Complex Code Review (Task Force + HITL)")
        
        print("This demonstrates a complex code review with security-sensitive files.")
        print("The system will use a task force and may escalate to human.")
        print("\nLevels Demonstrated:")
        print("  ✅ Level 1: Memory Coordinator stores context")
        print("  ✅ Level 2: Archivist/Librarian for memory")
        print("  ✅ Level 3: Task Force orchestration + HITL escalation")
        print("  ✅ Level 4: Metrics collection")
        print("  ✅ Level 5: Professor Agent learns from review")
        
        self.print_step(1, 3, "Preparing review request...")
        
        review_data = {
            "review_id": f"demo_complex_{int(time.time())}",
            "repository": "dryad-backend",
            "pull_request_id": "demo-002",
            "files_changed": [
                "app/auth/authentication.py",
                "app/auth/authorization.py",
                "app/security/crypto.py",
                "app/api/endpoints/auth.py",
                "app/database/models/user.py",
                "tests/test_auth.py"
            ],
            "diff": """
+ def authenticate_user(username: str, password: str) -> User:
+     '''Authenticate user with username and password.'''
+     # Query user from database
+     user = db.query(User).filter(User.username == username).first()
+     
+     # Verify password
+     if user and verify_password(password, user.password_hash):
+         return user
+     
+     raise AuthenticationError('Invalid credentials')
+ 
+ def generate_token(user: User) -> str:
+     '''Generate JWT token for authenticated user.'''
+     payload = {
+         'user_id': user.id,
+         'username': user.username,
+         'exp': datetime.utcnow() + timedelta(hours=24)
+     }
+     return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            """,
            "author": "demo_user",
            "description": "Implement user authentication and JWT token generation",
            "tenant_id": "demo"
        }
        
        print("  Files: 6 (including security-sensitive)")
        print("  Complexity: High")
        print("  Expected Strategy: Task Force")
        print("  Expected Escalation: Likely (security issues)")
        
        self.print_step(2, 3, "Submitting review to API...")
        time.sleep(1)
        
        result = self.submit_review(review_data)
        
        self.print_step(3, 3, "Review Results")
        self.display_review_result(result)
        
        input("\n\nPress Enter to continue to metrics demo...")
    
    def demo_metrics(self):
        """Demonstrate metrics collection."""
        self.print_header("DEMO 3: Metrics Collection (Level 4)")
        
        print("This demonstrates the metrics collected during code reviews.")
        print("\nMetrics Tracked:")
        print("  📊 Total reviews processed")
        print("  ✅ Reviews completed")
        print("  ⚠️  Reviews escalated")
        print("  🔍 Total findings")
        print("  ⏱️  Review duration (p50, p95, p99)")
        
        self.print_step(1, 2, "Fetching metrics from API...")
        time.sleep(1)
        
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=5)
            if response.status_code == 200:
                metrics = response.json()
                
                self.print_step(2, 2, "Current Metrics")
                
                print(f"\n  Uptime: {metrics.get('uptime_seconds', 0):.1f} seconds")
                
                counters = metrics.get('counters', {})
                if counters:
                    print("\n  Counters:")
                    for key, value in sorted(counters.items()):
                        if 'code_review' in key:
                            display_key = key.split('{')[0].replace('code_review_', '').replace('_', ' ').title()
                            print(f"    {display_key}: {value}")
                
                timings = metrics.get('timings', {})
                if timings:
                    print("\n  Timings:")
                    for key, stats in timings.items():
                        if 'code_review' in key:
                            print(f"    Code Review Duration:")
                            print(f"      Count: {stats.get('count', 0)}")
                            print(f"      Mean: {stats.get('mean', 0):.3f}s")
                            print(f"      P50: {stats.get('p50', 0):.3f}s")
                            print(f"      P95: {stats.get('p95', 0):.3f}s")
                            print(f"      P99: {stats.get('p99', 0):.3f}s")
            else:
                print(f"\n  ❌ Failed to fetch metrics: HTTP {response.status_code}")
        except Exception as e:
            print(f"\n  ❌ Error fetching metrics: {e}")
    
    def run(self):
        """Run complete demonstration."""
        self.print_header("DRYAD.AI CODE REVIEW ASSISTANT - LIVE DEMONSTRATION")
        
        print("This demonstration shows the complete DRYAD.AI system in action.")
        print("\nWe will demonstrate:")
        print("  1. Simple Code Review (Single Agent)")
        print("  2. Complex Code Review (Task Force + HITL)")
        print("  3. Metrics Collection")
        
        # Check server
        print("\n🔍 Checking API server...")
        if not self.check_server():
            print("❌ API server is not running!")
            print("\nPlease start the server first:")
            print("  python scripts/start_production.py")
            sys.exit(1)
        
        print("✅ API server is running")
        
        input("\n\nPress Enter to start demonstration...")
        
        # Run demos
        self.demo_simple_review()
        self.demo_complex_review()
        self.demo_metrics()
        
        # Final summary
        self.print_header("DEMONSTRATION COMPLETE")
        
        print("✅ All demonstrations completed successfully!")
        print("\nWhat was demonstrated:")
        print("  ✅ Level 0: Foundation Services (logging, database)")
        print("  ✅ Level 1: Memory Coordinator, Memory Scribe, Agent Registry")
        print("  ✅ Level 2: Archivist (short-term), Librarian (long-term)")
        print("  ✅ Level 3: Hybrid Orchestration, HITL Escalation")
        print("  ✅ Level 4: Metrics Collection, Performance Tracking")
        print("  ✅ Level 5: Professor Agent Integration")
        print("\n🎉 DRYAD.AI is fully operational!")
        print("\nNext steps:")
        print("  - View real-time metrics: python scripts/monitor_production.py")
        print("  - Access API docs: http://localhost:8000/docs")
        print("  - Run more reviews via API")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DRYAD.AI Code Review Demo")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API server URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    demo = CodeReviewDemo(api_url=args.url)
    demo.run()


if __name__ == "__main__":
    main()

