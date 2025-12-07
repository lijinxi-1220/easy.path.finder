from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .. import redis_client
from users.api.auth import auth_user_id
from core.utils import ok
from core.exceptions import BusinessError


@require_GET
def history(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    uid = auth_user_id(request)
    try:
        page = int(request.GET.get("page") or 1)
        page_size = int(request.GET.get("page_size") or 20)
    except Exception:
        page, page_size = 1, 20
    cur = redis_client.redis.get(f"chat:session:list:{uid}") or ""
    ids = [x for x in cur.split(",") if x]
    if not ids:
        raise BusinessError(5003, "no_history", 404)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    sessions = []
    for cid in ids[start:end]:
        msgs = (redis_client.redis.get(f"chat:messages:list:{cid}") or "").split(",")
        last_user = None
        last_assist = None
        for mid in msgs[::-1]:
            m = redis_client.redis.hgetall(f"chat:message:{mid}") or {}
            if m.get("role") == "assistant" and not last_assist:
                last_assist = m
            if m.get("role") == "user" and not last_user:
                last_user = m
            if last_user and last_assist:
                break
        sessions.append({
            "chat_id": cid,
            "message_content": (last_user or {}).get("message_content", ""),
            "reply_content": (last_assist or {}).get("reply_content", ""),
            "timestamp": (last_assist or last_user or {}).get("timestamp", ""),
        })
    return ok({"chats": sessions, "meta": {"total": len(ids), "page": page, "page_size": page_size}})
