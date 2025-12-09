from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .. import redis_client
from users.api.auth import auth_user_id, token_role, resolve_user_id
from core.utils import ok, err
import json


@require_GET
def optimize(request):
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    provided_uid = request.GET.get("user_id") or ""
    user_id = resolve_user_id(request, provided_uid)
    if not user_id:
        from core.exceptions import ErrorCode
        return err(ErrorCode.PERMISSION_DENIED)
    resume_id = request.GET.get("resume_id") or ""
    target_job = request.GET.get("target_job") or ""
    if not user_id or not resume_id:
        from core.exceptions import ErrorCode
        return err(ErrorCode.MISSING_PARAMS)
    r = redis_client.redis.hgetall(f"resume:id:{resume_id}")
    if not r or r.get("user_id") != user_id:
        return err(2004, "resume_not_found", status=404)
    parsed = json.loads(r.get("parsed_content") or "{}")
    suggestions = [
        {"title": "增强量化成果", "detail": "用数据描述业绩，例如提升率、节省成本"},
        {"title": "优化关键词", "detail": f"加入与 {target_job or '目标岗位'} 相关的关键词"},
        {"title": "精简长度", "detail": "控制在1-2页，突出核心亮点"},
    ]
    return ok({"optimization_suggestions": suggestions})
