import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from .. import redis_client
from .auth import issue_jwt
from core.ratelimit import allow
from core.utils import ok, err


@csrf_exempt
def login(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1003, "invalid_json")
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    phone = str(data.get("phone_number") or "").strip()
    password = data.get("password")
    if not password or (not username and not email and not phone):
        return err(1003, "missing_params")
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    # rate limit per IP
    ip = request.META.get("REMOTE_ADDR", "unknown")
    if not allow(redis_client.redis, f"rl:login:{ip}", limit=10, window_seconds=60):
        return err(1020, "rate_limited", status=429)
    user_id = None
    if username:
        user_id = redis_client.redis.get(f"user:username:{username}")
    elif email:
        user_id = redis_client.redis.get(f"user:email:{email}")
    elif phone:
        user_id = redis_client.redis.get(f"user:phone:{phone}")
    if not user_id:
        return err(1003, "invalid_credentials", status=401)
    user = redis_client.redis.hgetall(f"user:id:{user_id}")
    if not user:
        return err(1003, "invalid_credentials", status=401)
    if user.get("subscription_status") != "active":
        return err(1004, "account_inactive", status=403)
    if not check_password(password, user.get("password_hash", "")):
        return err(1003, "invalid_credentials", status=401)
    last_login_date = datetime.utcnow().isoformat()
    redis_client.redis.hset(f"user:id:{user_id}", mapping={"last_login_date": last_login_date})
    token = issue_jwt(user_id, user.get("role", "user"), user.get("username", username or email or phone))
    return ok({
        "user_id": user_id,
        "token": token,
        "last_login_date": last_login_date,
        "subscription_status": user.get("subscription_status", "active"),
    })
