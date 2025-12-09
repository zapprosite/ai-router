from locust import HttpUser, task, between

class RouterUser(HttpUser):
    wait_time = between(1, 3)

    @task(7)
    def simple_query(self):
        # Tier 1 (70%)
        self.client.post("/route", json={
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "prefer_code": False
        }, name="Tier1_Simple")

    @task(2)
    def code_query(self):
        # Tier 2 (20%)
        self.client.post("/route", json={
            "messages": [{"role": "user", "content": "Write a Python function for sorting."}],
            "prefer_code": True
        }, name="Tier2_Code")

    @task(1)
    def complex_query(self):
        # Tier 3 (10%)
        self.client.post("/route", json={
            "messages": [{"role": "user", "content": "Traceback most recent call last... Fix this error."}],
            "prefer_code": True
        }, name="Tier3_Complex")
