from datetime import datetime
from django.http import JsonResponse

from core.exceptions import ErrorCode
from core.utils import ok, err
from django.views.decorators.http import require_GET
from ..repo import ResumeRepo
from users.api.auth import auth_user_id, token_role
import json


@require_GET
def score(request):
    user_token_uid = auth_user_id(request)
    provided_uid = request.GET.get("user_id") or ""
    if provided_uid and provided_uid != user_token_uid:
        bearer = request.headers.get("Authorization", "")
        token = bearer.split(" ", 1)[1] if bearer.startswith("Bearer ") else ""
        if token_role(token) != "admin":
            return err(ErrorCode.PERMISSION_DENIED)
        user_id = provided_uid
    else:
        user_id = user_token_uid
    resume_id = request.GET.get("resume_id") or ""
    if not user_id or not resume_id:
        return err(ErrorCode.MISSING_PARAMS)
    r = ResumeRepo.get(resume_id)
    if not r or r.get("user_id") != user_id:
        return err(ErrorCode.RESUME_NOT_FOUND)
    parsed = json.loads(r.get("parsed_content") or "{}")
    size = int(parsed.get("size", 1000))
    # 简单评分：根据大小给出分数模拟
    overall = max(50, min(95, 60 + size // 5000))
    details = {
        "structure": overall - 5,
        "skills": overall - 3,
        "experience": overall - 2,
    }
    return ok({
        "overall_score": overall,
        "detail_scores": details,
        "generated_date": datetime.utcnow().isoformat(),
    })
