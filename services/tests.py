import json
from django.test import SimpleTestCase, Client
from users import redis_client as user_rc
from services import redis_client as svc_rc


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


class ServicesApiTests(SimpleTestCase):
    def setUp(self):
        fake = FakeRedis()
        user_rc.redis = fake
        svc_rc.redis = fake
        self.client = Client()
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
        svc_rc.redis.set("svc:course:list", "c1")
        svc_rc.redis.hset("svc:course:id:c1", mapping={"name": "Django Course", "intro": "Web dev", "provider": "Example", "link": "https://example.com"})
        svc_rc.redis.set("mentor:list:backend", "m1")
        svc_rc.redis.hset("mentor:id:m1", mapping={"name": "Bob", "title": "Senior", "years": "8", "fee": "100"})
        svc_rc.redis.set("project:list:exchange", "p1")
        svc_rc.redis.hset("project:id:p1", mapping={"name": "Global Exchange", "intro": "Intl", "time": "2026", "location": "US", "method": "apply"})

    def test_services_endpoints(self):
        r = self.client.get("/service/recommend?service_type=course", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/service/mentors?field=backend", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        r = self.client.post(
            "/service/consult",
            data=json.dumps({"mentor_id": "m1", "consult_topic": "topic", "consult_time": "2026-01-01"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/service/projects?project_type=exchange", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        r = self.client.post(
            "/service/subscription",
            data=json.dumps({"subscription_type": "month", "payment_info": {"channel": "mock"}}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)

