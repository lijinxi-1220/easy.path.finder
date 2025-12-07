import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from users.api.auth import token_role
from core.utils import ok, err


def _require_admin(request):
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
    return token_role(token) == "admin"


@csrf_exempt
def import_job_profiles(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    if not _require_admin(request):
        return err(1006, "permission_denied", status=403)
    try:
        items = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    ids = []
    for it in items if isinstance(items, list) else []:
        pid = it.get("job_profile_id") or it.get("id")
        jt = it.get("job_title") or ""
        ind = (it.get("industry") or "").lower()
        if not pid or not jt:
            continue
        redis_client.redis.hset(f"job:profile:{pid}", mapping={
            "job_profile_id": pid,
            "job_title": jt,
            "company": it.get("company", ""),
            "required_skills": json.dumps(it.get("required_skills", [])),
            "required_experience": it.get("required_experience", ""),
            "industry": it.get("industry", ""),
        })
        redis_client.redis.set(f"job:profile:index:{jt.lower()}:{ind}", pid)
        ids.append(pid)
    cur = redis_client.redis.get("job:profile:list") or ""
    existing = [x for x in cur.split(",") if x]
    merged = list(dict.fromkeys(existing + ids))
    redis_client.redis.set("job:profile:list", ",".join(merged))
    return ok({"imported": len(ids)})


@csrf_exempt
def import_schools(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    if not _require_admin(request):
        return err(1006, "permission_denied", status=403)
    try:
        items = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    ids = []
    for it in items if isinstance(items, list) else []:
        sid = it.get("school_id") or it.get("id")
        if not sid:
            continue
        redis_client.redis.hset(f"school:id:{sid}", mapping={
            "school_id": sid,
            "school_name": it.get("school_name", ""),
            "major": it.get("major", ""),
            "rank": it.get("rank", ""),
        })
        slug = it.get("slug") or it.get("school_name", "").lower().replace(" ", "-")
        redis_client.redis.set(f"school:index:{slug}", sid)
        ids.append(sid)
    cur = redis_client.redis.get("school:list") or ""
    existing = [x for x in cur.split(",") if x]
    merged = list(dict.fromkeys(existing + ids))
    redis_client.redis.set("school:list", ",".join(merged))
    return ok({"imported": len(ids)})
