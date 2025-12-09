import json
from django.test import SimpleTestCase, Client


class ServicesSortTests(SimpleTestCase):
    def setUp(self):
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
        import core
        rc = core.redis_client
        rc.set("mentor:list:backend", "m1,m2")
        rc.hset("mentor:id:m1", mapping={"name": "Bob", "title": "Senior", "years": "5", "fee": "100"})
        rc.hset("mentor:id:m2", mapping={"name": "Alice", "title": "Lead", "years": "8", "fee": "200"})

    def test_mentors_sort_years_desc(self):
        r = self.client.get(
            "/service/mentors?field=backend&sort_by=years&sort_order=desc&page=1&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert r.status_code == 200
        mentors = r.json()["mentors"]
        assert int(mentors[0]["years"]) >= int(mentors[-1]["years"])
