import json
from django.test import SimpleTestCase, Client


class MatchesErrorsTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_recommend_requires_auth(self):
        r = self.client.get("/match/recommend?preference=both")
        assert r.status_code == 400
        assert "code" in r.json()
