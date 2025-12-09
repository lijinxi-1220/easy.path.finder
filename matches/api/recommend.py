import json

from django.views.decorators.http import require_GET

from core.exceptions import ErrorCode
from core.utils import ok, err
from resumes import redis_client as resume_rc
from users.api.auth import auth_user_id
from ..repo import MatchesRepo


@require_GET
def recommend(request):
    uid = auth_user_id(request)
    preference = (request.GET.get("preference") or "both").lower()
    resume_id = request.GET.get("resume_id") or ""
    if not uid:
        return err(ErrorCode.USER_INFO_INCOMPLETE)

    resume_skills = []
    if resume_id and resume_rc.redis:
        r = resume_rc.redis.hgetall(f"resume:id:{resume_id}") or {}
        if r.get("user_id") != uid:
            return err(ErrorCode.USER_INFO_INCOMPLETE)
        try:
            parsed = json.loads(r.get("parsed_content") or "{}")
            rs = parsed.get("skills") or []
            if isinstance(rs, list):
                resume_skills = [str(s).lower() for s in rs]
        except json.JSONDecodeError:
            resume_skills = []

    jobs = []
    schools = []

    if preference in ("job", "both"):
        ids = MatchesRepo.get_job_ids()
        for pid in [x for x in ids if x]:
            data = MatchesRepo.get_job_profile(pid) or {}
            try:
                req_sk = json.loads(data.get("required_skills") or "[]")
            except json.JSONDecodeError:
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
        ids = MatchesRepo.get_school_ids()
        for sid in [x for x in ids if x]:
            data = MatchesRepo.get_school(sid) or {}
            schools.append({
                "school_name": data.get("school_name", ""),
                "major": data.get("major", ""),
                "rank": data.get("rank", ""),
            })
        if not schools:
            schools = [{"school_name": "Demo University", "major": "CS", "rank": "Top 50"}]

    return ok({"jobs": jobs, "schools": schools})
