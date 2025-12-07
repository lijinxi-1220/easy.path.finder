import json
from django.test import SimpleTestCase, Client
from users import redis_client as user_rc
from plans import redis_client as plans_rc
from userdata import redis_client as ud_rc


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


class UserDataApiTests(SimpleTestCase):
    def setUp(self):
        fake = FakeRedis()
        user_rc.redis = fake
        plans_rc.redis = fake
        ud_rc.redis = fake
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

    def test_privacy_history_progress(self):
        # privacy update
        r = self.client.put(
            "/user/privacy",
            data=json.dumps({"privacy_settings": {"share_data": False, "collect_limit": "minimal"}}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("privacy_settings", r.json())

        # seed history
        hid = "h1"
        ud_rc.redis.hset(f"user:history:id:{hid}", mapping={
            "history_id": hid,
            "user_id": self.user_id,
            "action_type": "task_completed",
            "action_content": "完成任务A",
            "timestamp": "2025-12-01T00:00:00Z",
        })
        ud_rc.redis.set(f"user:history:list:{self.user_id}", hid)
        r = self.client.get("/user/history", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json()["history"]) >= 1)

        # create goal & tasks and mark done
        r = self.client.post(
            "/plan/goals",
            data=json.dumps({"goal_name": "Offer", "target_date": "2026-01-01"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        gid = r.json()["goal_id"]
        r = self.client.post(
            "/plan/tasks/generate",
            data=json.dumps({"goal_id": gid}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        tid = r.json()["tasks"][0]["task_id"]
        self.client.put(
            "/plan/tasks",
            data=json.dumps({"task_id": tid, "status": "done"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        r = self.client.get(f"/user/progress?data_type=task_progress&goal_id={gid}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        self.assertIn("task_progress", r.json())

