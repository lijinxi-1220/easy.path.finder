from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .. import redis_client
from users.api.auth import auth_user_id
from resumes import redis_client as resume_rc
import json
from core.utils import ok, err


@require_GET
def recommend(request):
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    uid = auth_user_id(request)
    preference = (request.GET.get("preference") or "both").lower()
    resume_id = request.GET.get("resume_id") or ""
    if not uid:
        return err(3002, "user_info_incomplete")

    resume_skills = []
    if resume_id and resume_rc.redis:
        r = resume_rc.redis.hgetall(f"resume:id:{resume_id}") or {}
        if r.get("user_id") != uid:
            return err(3002, "user_info_incomplete")
        try:
            parsed = json.loads(r.get("parsed_content") or "{}")
            rs = parsed.get("skills") or []
            if isinstance(rs, list):
                resume_skills = [str(s).lower() for s in rs]
        except Exception:
            resume_skills = []

    jobs = []
    schools = []

    if preference in ("job", "both"):
        ids = (redis_client.redis.get("job:profile:list") or "").split(",")
        for pid in [x for x in ids if x]:
            data = redis_client.redis.hgetall(f"job:profile:{pid}") or {}
            req_sk = []
            try:
                req_sk = json.loads(data.get("required_skills") or "[]")
            except Exception:
                req_sk = []
            req_sk = [str(s).lower() for s in req_sk]
            overlap = len(set(req_sk) & set(resume_skills)) if resume_skills else 0
            base = 70
            score = base + min(25, overlap * 10)
            jobs.append({
                "job_title": data.get("job_title", ""),
                "company": data.get("company", ""),
                "match_percentage": score,
            })
        if not jobs:
            jobs = [{"job_title": "Software Engineer", "company": "Example", "match_percentage": 72}]

    if preference in ("school", "both"):
        ids = (redis_client.redis.get("school:list") or "").split(",")
        for sid in [x for x in ids if x]:
            data = redis_client.redis.hgetall(f"school:id:{sid}") or {}
            schools.append({
                "school_name": data.get("school_name", ""),
                "major": data.get("major", ""),
                "rank": data.get("rank", ""),
            })
        if not schools:
            schools = [{"school_name": "Demo University", "major": "CS", "rank": "Top 50"}]

    return ok({"jobs": jobs, "schools": schools})
