import json
from django.test import SimpleTestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
import core
from core.testing.fake_redis import FakeRedis




class ChatApiTests(SimpleTestCase):
    def setUp(self):
        core.redis_client = FakeRedis()
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
        # upload resume
        file = SimpleUploadedFile("resume.docx", b"fake-content")
        r = self.client.post(
            "/resume/upload",
            data={"resume_name": "My Resume", "resume_file": file, "skills": json.dumps(["Python","Django"])},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.resume_id = r.json()["resume_id"]

    def test_interact_guide_history(self):
        r = self.client.post(
            "/chat/interact",
            data=json.dumps({"message_content": "请帮我看看简历", "chat_scene": "resume"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        chat_id = r.json()["chat_id"]
        self.assertIn("reply_content", r.json())

        # continue in same session
        r2 = self.client.post(
            "/chat/interact",
            data=json.dumps({"message_content": "继续", "chat_scene": "resume", "chat_id": chat_id}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["chat_id"], chat_id)

        r = self.client.get(
            f"/chat/resume_guide?resume_id={self.resume_id}",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("guide_question", r.json())

        r = self.client.get(
            "/chat/history?page=1&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json().get("chats", [])) >= 1)
