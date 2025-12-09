import json
from django.test import SimpleTestCase, Client
import core
from core.testing.fake_redis import FakeRedis


class ServicesApiTests(SimpleTestCase):
    def setUp(self):
        core.redis_client = FakeRedis()
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
        rc = core.redis_client
        rc.set("svc:course:list", "c1")
        rc.hset("svc:course:id:c1", mapping={"name": "Django Course", "intro": "Web dev", "provider": "Example",
                                                 "link": "https://example.com"})
        rc.set("mentor:list:backend", "m1")
        rc.hset("mentor:id:m1", mapping={"name": "Bob", "title": "Senior", "years": "8", "fee": "100"})
        rc.set("project:list:exchange", "p1")
        rc.hset("project:id:p1",
                    mapping={"name": "Global Exchange", "intro": "Intl", "time": "2026", "location": "US",
                             "method": "apply"})

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

    def test_subscription_webhook(self):
        # prepare subscription
        self.client.post(
            "/service/subscription",
            data=json.dumps({"subscription_type": "month", "payment_info": {"channel": "mock"}}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        # send webhook
        import json as _json
        from core.security import verify_hmac
        from services.config import SUBSCRIPTION_WEBHOOK_SECRET
        body = _json.dumps({"user_id": "dummy", "status": "active"}).encode("utf-8")
        sig = __import__("hmac").new(SUBSCRIPTION_WEBHOOK_SECRET.encode(), body, __import__("hashlib").sha256).hexdigest()
        r = self.client.post(
            "/service/subscription/webhook",
            data=body,
            content_type="application/json",
            HTTP_X_SIGNATURE=sig,
        )
        self.assertEqual(r.status_code, 200)
