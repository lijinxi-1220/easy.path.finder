from django.http import JsonResponse
from django.views.decorators.http import require_GET
from users.api.auth import auth_user_id
from resumes import redis_client as resume_rc
import json
from core.utils import ok
from core.exceptions import BusinessError


@require_GET
def resume_guide(request):
    uid = auth_user_id(request)
    resume_id = request.GET.get("resume_id") or ""
    if not uid:
        raise BusinessError(1002, "missing_params", 400)
    r = resume_rc.redis.hgetall(f"resume:id:{resume_id}") if resume_rc.redis else {}
    if not r or r.get("user_id") != uid:
        raise BusinessError(2004, "resume_not_found", 404)
    parsed = {}
    try:
        parsed = json.loads(r.get("parsed_content") or "{}")
    except Exception:
        parsed = {}
    required_fields = ["skills", "education", "experience", "projects"]
    missing = [f for f in required_fields if not parsed.get(f)]
    guide_questions = [
        "请列出近两年的核心技能与熟练度",
        "请补充最高学历、毕业年份与专业",
        "请描述一段可量化的工作成果",
        "请描述一个关键项目的角色与贡献",
    ]
    return ok({"guide_question": guide_questions, "missing_field": missing})
