import json
from django.test import SimpleTestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from core import redis_client as user_rc




class ResumeApiTests(SimpleTestCase):
    def setUp(self):
        # share fake redis between user & resume for simplicity
        self.client = Client()

        # register a user and login to get token
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

    def test_upload_score_optimize_manage_export(self):
        # upload
        file = SimpleUploadedFile("resume.docx", b"fake-content")
        r = self.client.post(
            "/resume/upload",
            data={"resume_name": "My Resume", "resume_file": file, "skills": json.dumps(["Python","Django"])},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        resume_id = r.json()["resume_id"]

        # score
        r = self.client.get(
            f"/resume/score?resume_id={resume_id}",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)

        # optimize
        r = self.client.get(
            f"/resume/optimize?resume_id={resume_id}&target_job=Backend",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)

        # manage list
        r = self.client.get(
            f"/resume/manage",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json()["resumes"]) >= 1)

        # set default
        r = self.client.put(
            "/resume/manage",
            data=json.dumps({"resume_id": resume_id, "is_default": True}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["resume"]["is_default"], "1")

        # export
        r = self.client.post(
            "/resume/export",
            data={"resume_id": resume_id, "template_id": "basic", "export_format": "pdf"},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("export_url", r.json())
