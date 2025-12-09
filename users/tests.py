import json
from django.test import SimpleTestCase, Client

import core
from core.testing.fake_redis import FakeRedis
from users.repo import UsersRepo


class UserApiTests(SimpleTestCase):
    def setUp(self):
        core.redis_client = FakeRedis()
        self.client = Client()

    def test_register_login_profile_logout(self):
        r = self.client.post(
            "/register",
            data=json.dumps({
                "username": "alice",
                "password": "pass123",
                "email": "a@x.com",
                "phone_number": "123",
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        reg = r.json()
        uid = reg["user_id"]
        token = reg["token"]

        r = self.client.post(
            "/login",
            data=json.dumps({"username": "alice", "password": "pass123"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        token = r.json()["token"]

        r = self.client.get(f"/profile/{uid}", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(r.status_code, 200)

        r = self.client.put(
            f"/profile/{uid}",
            data=json.dumps({"full_name": "Alice"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["full_name"], "Alice")

        r = self.client.post("/logout", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])

        r = self.client.get(f"/profile/{uid}", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(r.status_code, 401)

    def test_send_code_and_login_code(self):
        r = self.client.post(
            "/register",
            data=json.dumps({
                "username": "bob",
                "password": "pass456",
                "email": "b@x.com",
                "phone_number": "555",
            }),
            content_type="application/json",
        )
        uid = r.json()["user_id"]
        # request code
        r = self.client.post(
            "/send_code",
            data=json.dumps({"email": "b@x.com"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        # read code from fake storage
        code = UsersRepo.client().get("otp:email:b@x.com")
        # login via code
        r = self.client.post(
            "/login/code",
            data=json.dumps({"email": "b@x.com", "code": code}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        token = r.json()["token"]
        # access profile
        r = self.client.get(f"/profile/{uid}", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(r.status_code, 200)
