"""
Basic Locust load test placeholder
"""
from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        """Basic health check load test"""
        self.client.get("/health")

    @task
    def stats_check(self):
        """Basic stats endpoint load test"""
        self.client.get("/stats")