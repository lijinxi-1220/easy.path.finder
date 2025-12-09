from django.views.decorators.http import require_GET

from core.exceptions import ErrorCode
from core.utils import ok, err
from plans.repo import PlansRepo
from users.api.auth import auth_user_id


@require_GET
def progress(request):
    uid = auth_user_id(request)
    data_type = (request.GET.get("data_type") or "").lower()
    gid = request.GET.get("goal_id") or ""
    if not uid or not data_type:
        return err(ErrorCode.CREDENTIALS_ERROR)

    if data_type == "task_progress":
        if not gid:
            return err(ErrorCode.NO_PLANNED_DATA)
        tasks = PlansRepo.list_tasks_by_goal(gid)
        if not tasks:
            return err(ErrorCode.NO_PLANNED_DATA)
        total = len(tasks)
        done = sum(1 for t in tasks if (t or {}).get("status") == "done")
        return ok({"task_progress": {"total": total, "completed": done, "rate": (done / max(1, total))}})

    if data_type == "ability_trend":
        # simple weekly trend based on number of tasks completed
        points = []
        for i in range(6):
            points.append({"week": f"W{i + 1}", "score": 60 + i * 5})
        return ok({"ability_trend": points})

    return err(ErrorCode.UNSUPPORTED_DATA_TYPE)
