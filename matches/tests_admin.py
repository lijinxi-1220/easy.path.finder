import json
from django.test import SimpleTestCase, Client
from users.api.auth import issue_jwt


class MatchesAdminTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        # register & login (for user flow not strictly required here)
        self.client.post(
            "/register",
            data=json.dumps({"username": "admin", "password": "pass123"}),
            content_type="application/json",
        )
        r = self.client.post(
            "/login",
            data=json.dumps({"username": "admin", "password": "pass123"}),
            content_type="application/json",
        )
        self.user_id = r.json()["user_id"]
        # forge admin token
        self.admin_token = issue_jwt(self.user_id, "admin", "admin")

    def test_import_job_profiles_and_schools(self):
        jobs = [{
            "job_profile_id": "job-2",
            "job_title": "Backend Engineer",
            "company": "ACME",
            "required_skills": ["Python", "Django"],
            "required_experience": "3+ years",
            "industry": "software"
        }]
        r = self.client.post(
            "/match/admin/job_profiles/import",
            data=json.dumps(jobs),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )
        assert r.status_code == 200
        schools = [{
            "school_id": "school-2",
            "school_name": "Example U",
            "major": "CS",
            "rank": "Top 100",
            "slug": "example-u"
        }]
        r = self.client.post(
            "/match/admin/schools/import",
            data=json.dumps(schools),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )
        assert r.status_code == 200
