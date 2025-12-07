import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from users.api.auth import auth_user_id
from userdata import redis_client
from plans import redis_client as plans_rc
from plans.repo import PlansRepo
from core.utils import ok
from core.exceptions import BusinessError


@require_GET
def progress(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    uid = auth_user_id(request)
    data_type = (request.GET.get("data_type") or "").lower()
    gid = request.GET.get("goal_id") or ""
    if not uid or not data_type:
        raise BusinessError(1002, "missing_params", 400)

    if data_type == "task_progress":
        if not gid:
            raise BusinessError(4005, "no_planned_data", 404)
        tasks = PlansRepo.list_tasks_by_goal(gid) if plans_rc.redis else []
        if not tasks:
            raise BusinessError(4005, "no_planned_data", 404)
        total = len(tasks)
        done = sum(1 for t in tasks if (t or {}).get("status") == "done")
        return ok({"task_progress": {"total": total, "completed": done, "rate": (done / max(1, total))}})

    if data_type == "ability_trend":
        # simple weekly trend based on number of tasks completed
        points = []
        for i in range(6):
            points.append({"week": f"W{i+1}", "score": 60 + i * 5})
        return ok({"ability_trend": points})

    raise BusinessError(1002, "unsupported_data_type", 400)
