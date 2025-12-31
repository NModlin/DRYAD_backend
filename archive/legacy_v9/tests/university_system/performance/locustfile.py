"""
Performance testing scenarios for Uni0 University System using Locust
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import json
import random
import time

# Test data
TEST_UNIVERSITIES = [
    {"id": "uni-001", "name": "Test University 1"},
    {"id": "uni-002", "name": "Test University 2"},
    {"id": "uni-003", "name": "Test University 3"},
]

TEST_AGENTS = [
    {"id": "agent-001", "name": "Agent 1"},
    {"id": "agent-002", "name": "Agent 2"},
    {"id": "agent-003", "name": "Agent 3"},
]


class Uni0User(HttpUser):
    """Base user class for Uni0 performance testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.auth_token = None
        self.university_id = None
        self.agent_id = None
        self.login()
    
    def login(self):
        """Authenticate and get access token"""
        university = random.choice(TEST_UNIVERSITIES)
        self.university_id = university["id"]
        
        login_data = {
            "university_id": self.university_id,
            "api_key": f"uni0_{self.university_id}_key"
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=login_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Login failed with status {response.status_code}")
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.auth_token}"
        } if self.auth_token else {}
    
    @task(3)
    def list_universities(self):
        """List all universities"""
        with self.client.get(
            "/api/v1/universities/",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def get_university(self):
        """Get a specific university"""
        university = random.choice(TEST_UNIVERSITIES)
        with self.client.get(
            f"/api/v1/universities/{university['id']}",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def create_university(self):
        """Create a new university"""
        university_data = {
            "name": f"Test University {random.randint(1000, 9999)}",
            "description": "Performance test university",
            "owner_user_id": "test-owner",
            "max_agents": 100
        }
        
        with self.client.post(
            "/api/v1/universities/",
            json=university_data,
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def get_university_stats(self):
        """Get university statistics"""
        university = random.choice(TEST_UNIVERSITIES)
        with self.client.get(
            f"/api/v1/universities/{university['id']}/stats",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def get_university_agents(self):
        """Get agents for a university"""
        university = random.choice(TEST_UNIVERSITIES)
        with self.client.get(
            f"/api/v1/universities/{university['id']}/agents",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def health_check(self):
        """Check system health"""
        with self.client.get(
            "/api/v1/health/",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """Get Prometheus metrics"""
        with self.client.get(
            "/api/v1/health/metrics",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class HighLoadUser(Uni0User):
    """High load user - makes more requests"""
    wait_time = between(0.5, 1.5)


class LowLoadUser(Uni0User):
    """Low load user - makes fewer requests"""
    wait_time = between(3, 5)


# Event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("\n" + "="*50)
    print("Performance Test Started")
    print("="*50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\n" + "="*50)
    print("Performance Test Completed")
    print("="*50)
    
    # Print statistics
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")

