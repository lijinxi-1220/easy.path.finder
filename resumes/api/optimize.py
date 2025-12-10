import json

from django.views.decorators.http import require_GET

from core.exceptions import ErrorCode
from core.utils import ok, err
from users.api.auth import resolve_user_id
from ..repo import ResumeRepo


@require_GET
def optimize(request):
    provided_uid = request.GET.get("user_id") or ""
    user_id = resolve_user_id(request, provided_uid)
    if not user_id:
        return err(ErrorCode.PERMISSION_DENIED)
    resume_id = request.GET.get("resume_id") or ""
    target_job = request.GET.get("target_job") or ""
    if not user_id or not resume_id:
        return err(ErrorCode.MISSING_PARAMS)
    r = ResumeRepo.get(resume_id)
    if not r or r.get("user_id") != user_id:
        return err(ErrorCode.RESUME_NOT_FOUND)
    # parsed = json.loads(r.get("parsed_content") or "{}")
    suggestions = [
        {"title": "增强量化成果", "detail": "用数据描述业绩，例如提升率、节省成本"},
        {"title": "优化关键词", "detail": f"加入与 {target_job or '目标岗位'} 相关的关键词"},
        {"title": "精简长度", "detail": "控制在1-2页，突出核心亮点"},
    ]
    return ok({"optimization_suggestions": suggestions})
