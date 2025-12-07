import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from services import redis_client
from core.ratelimit import allow
from core.utils import ok
from core.validators import validate_body
from core.exceptions import BusinessError
from core.idempotency import ensure
from users.api.auth import auth_user_id


@csrf_exempt
@validate_body({
    "props": {
        "mentor_id": {"type": "str", "required": True},
        "consult_topic": {"type": "str"},
        "consult_time": {"type": "iso-datetime"},
    }
})
def consult(request):
    if request.method != "POST":
        raise BusinessError(405, "method_not_allowed", 405)
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    uid = auth_user_id(request)
    v = getattr(request, "validated_body", {})
    mentor_id = v.get("mentor_id")
    topic = v.get("consult_topic")
    time = v.get("consult_time")
    if not uid or not mentor_id:
        raise BusinessError(6004, "duplicate_or_invalid", 400)
    # rate-limit per user
    if not allow(redis_client.redis, f"rl:consult:{uid}", limit=3, window_seconds=3600):
        raise BusinessError(1020, "rate_limited", 429)
    m = redis_client.redis.hgetall(f"mentor:id:{mentor_id}") or {}
    if not m:
        raise BusinessError(6003, "mentor_not_found", 404)
    # prevent duplicate by user+mentor+time
    idx_key = f"consult:idx:{uid}:{mentor_id}:{time or ''}"
    if redis_client.redis.get(idx_key):
        raise BusinessError(6004, "duplicate_or_invalid", 400)
    idem = request.headers.get("Idempotency-Key")
    if not ensure(redis_client.redis, "consult", f"{uid}:{idem}" if idem else "", ttl_seconds=3600):
        raise BusinessError(6004, "duplicate_or_invalid", 400)
    app_id = str(uuid.uuid4())
    redis_client.redis.hset(f"consult:id:{app_id}", mapping={
        "application_id": app_id,
        "user_id": uid,
        "mentor_id": mentor_id,
        "consult_topic": topic or "",
        "consult_time": time or "",
        "application_status": "submitted",
        "feedback": "",
    })
    redis_client.redis.set(idx_key, app_id, ex=3600)
    return ok(redis_client.redis.hgetall(f"consult:id:{app_id}") or {})
