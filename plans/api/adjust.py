import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from users.api.auth import auth_user_id
from core.utils import ok, err


@csrf_exempt
def adjust(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    uid = auth_user_id(request)
    gid = body.get("goal_id")
    completion = body.get("task_completion") or []
    g = redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {}
    if not g or g.get("user_id") != uid:
        return err(4001, "goal_not_found", status=404)
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
    redis_client.redis.hset(f"plan:goal:id:{gid}", mapping={"status": new_status})
    # 返回调整后的目标与简要说明
    return ok({
        "adjusted_goal": redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {},
        "adjustment_reason": f"completion_rate={int(rate)}%",
        "updated_at": datetime.utcnow().isoformat(),
    })
