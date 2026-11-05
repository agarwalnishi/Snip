import random

from locust import HttpUser, between, task

CODES = open("loadtest/codes.txt").read().split()
HOT = CODES[:200]


class Visitor(HttpUser):
    wait_time = between(0.01, 0.05)

    @task(90)
    def hot(self):
        self.client.get(f"/{random.choice(HOT)}", allow_redirects=False, name="/[code] hot")

    @task(8)
    def cold(self):
        self.client.get(f"/{random.choice(CODES)}", allow_redirects=False, name="/[code] cold")

    @task(2)
    
    def missing(self):
        self.client.get(f"/zz{random.randint(0, 99999):05d}", allow_redirects=False, name="/[code] missing")