import json
from datetime import datetime, UTC

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.utils import ok, err
from plans.repo import PlansRepo
from users.api.auth import auth_user_id


@csrf_exempt
@require_POST
def adjust(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    uid = auth_user_id(request)
    gid = body.get("goal_id")
    completion = body.get("task_completion") or []
    g = PlansRepo.get_goal(gid) or {}
    if not g or g.get("user_id") != uid:
        return err(ErrorCode.GOAL_NOT_FOUND)
    # 简化：若完成率高则将状态设为 progressing 或 completed
    try:
        rate = (sum(1 for it in completion if it.get("status") == "done") / max(1, len(completion))) * 100
    except Exception:
        rate = 0
    new_status = "active"
    if rate >= 80:
        new_status = "completed"
    elif rate >= 30:
        new_status = "progressing"
    PlansRepo.update_goal(gid, mapping={"status": new_status})
    # 返回调整后的目标与简要说明
    return ok({
        "adjusted_goal": PlansRepo.get_goal(gid) or {},
        "adjustment_reason": f"completion_rate={int(rate)}%",
        "updated_at": datetime.now(UTC).isoformat(),
    })
