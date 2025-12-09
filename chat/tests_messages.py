import json
from django.test import SimpleTestCase, Client


class ChatMessagesTests(SimpleTestCase):
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

    def test_messages_pagination(self):
        r1 = self.client.post(
            "/chat/interact",
            data=json.dumps({"message_content": "hi", "chat_scene": "general"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        chat_id = r1.json()["chat_id"]
        # second message
        self.client.post(
            "/chat/interact",
            data=json.dumps({"message_content": "again", "chat_scene": "general", "chat_id": chat_id}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        r = self.client.get(
            f"/chat/messages?chat_id={chat_id}&page=1&page_size=1",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        body = r.json()
        assert "messages" in body and len(body["messages"]) == 1
        assert "meta" in body and body["meta"]["page_size"] == 1
