import json
from django.test import SimpleTestCase, Client
from users import redis_client as user_rc
from resumes import redis_client as resume_rc
from matches import redis_client as match_rc
from django.core.files.uploadedfile import SimpleUploadedFile


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


class MatchApiTests(SimpleTestCase):
    def setUp(self):
        fake = FakeRedis()
        user_rc.redis = fake
        resume_rc.redis = fake
        match_rc.redis = fake
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

        # create a resume
        file = SimpleUploadedFile("resume.docx", b"fake-content")
        r = self.client.post(
            "/resume/upload",
            data={"resume_name": "My Resume", "resume_file": file},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.resume_id = r.json()["resume_id"]

        # seed job & school profiles
        match_rc.redis.set("job:profile:index:software engineer:", "job-1")
        match_rc.redis.hset("job:profile:job-1", mapping={
            "job_profile_id": "job-1",
            "job_title": "Software Engineer",
            "company": "Example Co",
            "required_skills": json.dumps(["Python", "Django"]),
            "required_experience": "2+ years",
        })
        match_rc.redis.set("job:profile:list", "job-1")
        match_rc.redis.set("school:index:demo-u", "school-1")
        match_rc.redis.hset("school:id:school-1", mapping={
            "school_id": "school-1",
            "school_name": "Demo University",
            "major": "CS",
            "rank": "Top 50",
        })
        match_rc.redis.set("school:list", "school-1")

        # skills 已在上传环节提供

    def test_job_profile_and_details(self):
        r = self.client.get("/match/job_profile?job_title=Software%20Engineer", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        pid = r.json()["job_profile_id"]
        r = self.client.get(f"/match/job_detail?job_profile_id={pid}", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)

    def test_school_detail(self):
        r = self.client.get("/match/school_detail?school_id=school-1", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)

    def test_match_analysis_and_recommend(self):
        r = self.client.post(
            "/match/analysis",
            data=json.dumps({"resume_id": self.resume_id, "target_type": "job", "target_id": "job-1"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("match_id", r.json())

        r = self.client.get("/match/recommend?preference=both", HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json().get("jobs", [])) >= 1)
        self.assertTrue(len(r.json().get("schools", [])) >= 1)
