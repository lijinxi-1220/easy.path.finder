import json
from django.test import SimpleTestCase, Client
from users import redis_client as user_rc
from plans import redis_client as plans_rc


class FakeRedis:
    def __init__(self):
        self.kv = {}
        self.hash = {}
    def set(self, k, v, ex=None):
        self.kv[k] = v
        return True
    def get(self, k):
        return self.kv.get(k)
    def exists(self, k):
        return 1 if k in self.kv else 0
    def hset(self, k, mapping=None, **kwargs):
        m = mapping or kwargs
        self.hash.setdefault(k, {})
        self.hash[k].update(m)
        return True
    def hgetall(self, k):
        return self.hash.get(k, {})
    def delete(self, k):
        return 1 if self.kv.pop(k, None) is not None else 0


class PlansApiTests(SimpleTestCase):
    def setUp(self):
        fake = FakeRedis()
        user_rc.redis = fake
        plans_rc.redis = fake
        self.client = Client()
        # register & login
        self.client.post(
            "/register",
            data=json.dumps({
                "username": "alice",
                "password": "pass123",
                "email": "a@x.com",
                "phone_number": "123",
            }),
            content_type="application/json",
        )
        r = self.client.post(
            "/login",
            data=json.dumps({"username": "alice", "password": "pass123"}),
            content_type="application/json",
        )
        self.user_id = r.json()["user_id"]
        self.token = r.json()["token"]

    def test_goals_tasks_plan_doc_adjust(self):
        # create goal
        r = self.client.post(
            "/plan/goals",
            data=json.dumps({"goal_name": "Offer in 3 months", "target_date": "2026-01-01"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        gid = r.json()["goal_id"]

        # list goals
        r = self.client.get("/plan/goals", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json()["goals"]) >= 1)

        # generate tasks
        r = self.client.post(
            "/plan/tasks/generate",
            data=json.dumps({"goal_id": gid}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        tasks = r.json()["tasks"]
        tid = tasks[0]["task_id"]

        # manage tasks: mark done
        r = self.client.put(
            "/plan/tasks",
            data=json.dumps({"task_id": tid, "status": "done"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "done")

        # pagination and filtering
        # add two more tasks
        for i in range(2):
            self.client.post(
                "/plan/tasks",
                data=json.dumps({"goal_id": gid, "task_name": f"Extra {i}", "priority": "low"}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {self.token}",
            )
        r = self.client.get(f"/plan/tasks?goal_id={gid}&page=1&page_size=2&sort_by=created_at&sort_order=desc",
                            HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["tasks"]), 2)
        r = self.client.get(f"/plan/tasks?goal_id={gid}&status=done",
                            HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(t["status"] == "done" for t in r.json()["tasks"]))

        # plan doc
        r = self.client.get(f"/plan/doc?goal_id={gid}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        self.assertIn("plan_doc_url", r.json())

        # adjust route
        r = self.client.post(
            "/plan/adjust",
            data=json.dumps({"goal_id": gid, "task_completion": [{"task_id": tid, "status": "done"}]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("adjusted_goal", r.json())
