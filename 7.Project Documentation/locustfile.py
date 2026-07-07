import random
from locust import HttpUser, task, between

class SmartLenderLoadTest(HttpUser):
    # Simulate a user waiting between 1 to 3 seconds between actions
    wait_time = between(1, 3)

    @task(2)
    def view_dashboard(self):
        """Simulate viewing the dashboard / history log"""
        self.client.get("/")

    @task(2)
    def view_submit_form(self):
        """Simulate viewing the loan submission page"""
        self.client.get("/submit")

    @task(5)
    def submit_loan_application(self):
        """Simulate submitting a loan prediction request"""
        # Generate semi-random profiles to simulate realistic usage
        payload = {
            "gender": random.choice(["Male", "Female"]),
            "married": random.choice(["Yes", "No"]),
            "dependents": random.choice(["0", "1", "2", "3+"]),
            "education": random.choice(["Graduate", "Not Graduate"]),
            "self_employed": random.choice(["Yes", "No"]),
            "applicant_income": str(random.randint(1500, 12000)),
            "coapplicant_income": str(random.choice([0, random.randint(500, 5000)])),
            "loan_amount": str(random.randint(50, 400)),
            "loan_amount_term": random.choice(["180", "360", "480"]),
            "credit_history": random.choice(["Good", "Bad"]),
            "property_area": random.choice(["Urban", "Semiurban", "Rural"])
        }
        
        self.client.post("/predict", data=payload)
