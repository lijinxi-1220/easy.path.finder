from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .. import redis_client
from users.api.auth import auth_user_id
from core.utils import ok, err


@require_GET
def plan_doc(request):
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    uid = auth_user_id(request)
    gid = request.GET.get("goal_id") or ""
    if gid:
        g = redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {}
        if not g or g.get("user_id") != uid:
            return err(4001, "goal_not_found", status=404)
    # 汇总近期任务与目标，生成摘要
    content = {
        "summary": "基于目标与任务的个性化规划摘要",
        "generated_at": datetime.utcnow().isoformat(),
    }
    url = "https://example.com/plan/doc/mock.pdf"
    return ok({"plan_doc_url": url, "plan_content": content})
