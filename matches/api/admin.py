import json

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.utils import ok, err
from users.api.auth import token_role
from ..repo import MatchesRepo


def _require_admin(request):
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
    return token_role(token) == "admin"


@csrf_exempt
@require_POST
def import_job_profiles(request):
    if not _require_admin(request):
        return err(ErrorCode.PERMISSION_DENIED)
    try:
        items = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    ids = []
    for it in items if isinstance(items, list) else []:
        pid = it.get("job_profile_id") or it.get("id")
        jt = it.get("job_title") or ""
        ind = (it.get("industry") or "").lower()
        if not pid or not jt:
            continue
        MatchesRepo.set_job_profile(pid, mapping={
            "job_profile_id": pid,
            "job_title": jt,
            "company": it.get("company", ""),
            "required_skills": json.dumps(it.get("required_skills", [])),
            "required_experience": it.get("required_experience", ""),
            "industry": it.get("industry", ""),
        })
        MatchesRepo.set_job_index(jt.lower(), ind, pid)
        ids.append(pid)
    for pid in ids:
        MatchesRepo.add_job_to_list(pid)
    return ok({"imported": len(ids)})


@csrf_exempt
@require_POST
def import_schools(request):
    if not _require_admin(request):
        return err(ErrorCode.PERMISSION_DENIED)
    try:
        items = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    ids = []
    for it in items if isinstance(items, list) else []:
        sid = it.get("school_id") or it.get("id")
        if not sid:
            continue
        MatchesRepo.set_school(sid, mapping={
            "school_id": sid,
            "school_name": it.get("school_name", ""),
            "major": it.get("major", ""),
            "rank": it.get("rank", ""),
        })
        slug = it.get("slug") or it.get("school_name", "").lower().replace(" ", "-")
        MatchesRepo.set_school_index(slug, sid)
        ids.append(sid)
    for sid in ids:
        MatchesRepo.add_school_to_list(sid)
    return ok({"imported": len(ids)})
