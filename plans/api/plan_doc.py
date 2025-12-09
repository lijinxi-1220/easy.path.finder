from datetime import datetime, UTC

from django.views.decorators.http import require_GET

from core.exceptions import ErrorCode
from core.utils import ok, err
from plans.repo import PlansRepo
from users.api.auth import auth_user_id


@require_GET
def plan_doc(request):
    uid = auth_user_id(request)
    gid = request.GET.get("goal_id") or ""
    if gid:
        g = PlansRepo.get_goal(gid) or {}
        if not g or g.get("user_id") != uid:
            return err(ErrorCode.GOAL_NOT_FOUND)
    # 汇总近期任务与目标，生成摘要
    content = {
        "summary": "基于目标与任务的个性化规划摘要",
        "generated_at": datetime.now(UTC).isoformat(),
    }
    url = "https://example.com/plan/doc/mock.pdf"
    return ok({"plan_doc_url": url, "plan_content": content})
