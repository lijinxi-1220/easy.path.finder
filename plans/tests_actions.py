import json
from django.test import SimpleTestCase, Client


class PlansActionsTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        # register & login
        self.client.post(
            "/register",
            data=json.dumps({"username": "alice", "password": "pass123"}),
            content_type="application/json",
        )
        r = self.client.post(
            "/login",
            data=json.dumps({"username": "alice", "password": "pass123"}),
            content_type="application/json",
        )
        self.token = r.json()["token"]

    def test_goals_tasks_actions(self):
        # create goal
        r = self.client.post(
            "/plan/goals",
            data=json.dumps({"goal_name": "Offer", "target_date": "2026-01-01"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        gid = r.json()["goal_id"]

        # list goals via action=list
        r = self.client.post(
            "/plan/goals",
            data=json.dumps({"action": "list", "status": "active", "page": 1, "page_size": 10}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        assert len(r.json()["goals"]) >= 1

        # generate tasks via action=generate
        r = self.client.post(
            "/plan/tasks",
            data=json.dumps({"action": "generate", "goal_id": gid}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        tasks = r.json()["tasks"]
        assert len(tasks) >= 1

        # list tasks via action=list
        r = self.client.post(
            "/plan/tasks",
            data=json.dumps({"action": "list", "goal_id": gid, "status": "pending", "page": 1, "page_size": 5}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        assert "tasks" in r.json()
