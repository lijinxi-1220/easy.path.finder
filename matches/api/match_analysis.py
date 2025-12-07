import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from ..repo import MatchesRepo
from users.api.auth import auth_user_id, token_role
from resumes import redis_client as resume_rc
from core.utils import ok, err


@csrf_exempt
def match_analysis(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    user_token_uid = auth_user_id(request)
    provided_uid = body.get("user_id")
    resume_id = body.get("resume_id")
    target_type = (body.get("target_type") or "").lower()
    target_id = body.get("target_id")
    if provided_uid and provided_uid != user_token_uid:
        bearer = request.headers.get("Authorization", "")
        token = bearer.split(" ", 1)[1] if bearer.startswith("Bearer ") else ""
        if token_role(token) != "admin":
            return err(1006, "permission_denied", status=403)
        user_id = provided_uid
    else:
        user_id = user_token_uid
    if not user_id or not resume_id or not target_type:
        return err(3002, "user_info_incomplete")
    r = resume_rc.redis.hgetall(f"resume:id:{resume_id}") if resume_rc.redis else {}
    if not r or r.get("user_id") != user_id:
        return err(3002, "user_info_incomplete")
    if target_type == "job":
        exists = bool(MatchesRepo.get_job_profile(target_id)) if target_id else True
        if not exists:
            return err(3003, "target_not_found", status=404)
    elif target_type == "school":
        exists = bool(MatchesRepo.get_school(target_id)) if target_id else True
        if not exists:
            return err(3003, "target_not_found", status=404)
    else:
        return err(1002, "invalid_target_type")

    # 简易匹配：根据简历长度与目标类型给出百分比
    parsed_size = 1000
    try:
        parsed = json.loads(r.get("parsed_content") or "{}")
        parsed_size = int(parsed.get("size", 1000))
    except Exception:
        parsed_size = 1000
    base = 60 if target_type == "job" else 65
    percentage = max(50, min(97, base + parsed_size // 5000))
    details = {
        "skills": percentage - 3,
        "experience": percentage - 5,
        "education": percentage - 6,
    }
    match_id = str(uuid.uuid4())
    redis_client.redis.hset(
        f"match:id:{match_id}",
        mapping={
            "match_id": match_id,
            "user_id": user_id,
            "resume_id": resume_id,
            "target_type": target_type,
            "target_id": target_id or "",
            "match_percentage": str(percentage),
            "match_details": json.dumps(details),
            "generated_date": datetime.utcnow().isoformat(),
        },
    )
    return ok({
        "match_id": match_id,
        "match_percentage": percentage,
        "match_details": details,
    })
