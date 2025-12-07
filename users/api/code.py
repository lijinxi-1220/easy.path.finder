import json
import secrets
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from .auth import issue_jwt
from .util import identifier_keys
from core.ratelimit import allow
from core.utils import ok, err


@csrf_exempt
def send_code(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    email = (body.get("email") or "").strip()
    phone = str(body.get("phone_number") or "").strip()
    if not email and not phone:
        return err(1002, "missing_params")
    otp_key, user_index_key = identifier_keys(email=email if email else None, phone=phone if phone else None)
    user_id = redis_client.redis.get(user_index_key)
    if not user_id:
        return err(1005, "user_not_found", status=404)
    rl_key = f"otp:rl:{user_index_key}"
    if redis_client.redis.get(rl_key):
        return err(1020, "rate_limited", status=429)
    # global rate limit per IP
    ip = request.META.get("REMOTE_ADDR", "unknown")
    if not allow(redis_client.redis, f"rl:otp:{ip}", limit=5, window_seconds=60):
        return err(1020, "rate_limited", status=429)
    code = f"{secrets.randbelow(1000000):06d}"
    redis_client.redis.set(otp_key, code, ex=300)
    redis_client.redis.set(rl_key, 1, ex=60)
    return ok({"success": True})


@csrf_exempt
def login_code(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1003, "invalid_json")
    email = (body.get("email") or "").strip()
    phone = str(body.get("phone_number") or "").strip()
    code = (body.get("code") or "").strip()
    if not code or (not email and not phone):
        return err(1003, "missing_params")
    otp_key, user_index_key = identifier_keys(email=email if email else None, phone=phone if phone else None)
    expect = redis_client.redis.get(otp_key)
    if not expect or expect != code:
        return err(1012, "code_invalid", status=401)
    user_id = redis_client.redis.get(user_index_key)
    if not user_id:
        return err(1005, "user_not_found", status=404)
    user = redis_client.redis.hgetall(f"user:id:{user_id}") or {}
    if user.get("subscription_status") != "active":
        return err(1004, "account_inactive", status=403)
    token = issue_jwt(user_id, user.get("role", "user"), user.get("username", email or phone))
    redis_client.redis.delete(otp_key)
    last_login_date = datetime.utcnow().isoformat()
    redis_client.redis.hset(f"user:id:{user_id}", mapping={"last_login_date": last_login_date})
    return ok({
        "user_id": user_id,
        "token": token,
        "last_login_date": last_login_date,
        "subscription_status": user.get("subscription_status", "active"),
    })
