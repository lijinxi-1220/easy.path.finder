import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .. import redis_client
from .auth import issue_jwt
from core.utils import ok, err
from core.idempotency import ensure
from core.exceptions import BusinessError


@csrf_exempt
def register(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    username = (data.get("username") or "").strip()
    password = data.get("password")
    email = data.get("email")
    phone = data.get("phone_number")
    if not username or not password:
        raise BusinessError(1002, "missing_params", 400)
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    if redis_client.redis.exists(f"user:username:{username}"):
        raise BusinessError(1001, "username_exists", 409)
    idem = request.headers.get("Idempotency-Key")
    from core.idempotency import ensure as _ensure
    if not _ensure(redis_client.redis, "register", f"{username}:{idem}" if idem else "", ttl_seconds=3600):
        raise BusinessError(1021, "duplicate_request", 409)
    user_id = str(uuid.uuid4())
    registration_date = datetime.utcnow().isoformat()
    password_hash = make_password(password)
    redis_client.redis.set(f"user:username:{username}", user_id)
    if email:
        redis_client.redis.set(f"user:email:{email}", user_id)
    if phone:
        redis_client.redis.set(f"user:phone:{phone}", user_id)
    redis_client.redis.hset(
        f"user:id:{user_id}",
        mapping={
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "email": email or "",
            "phone_number": phone or "",
            "registration_date": registration_date,
            "last_login_date": "",
            "subscription_status": "active",
            "role": "user",
            "full_name": "",
            "gender": "",
            "avatar_url": "",
        },
    )
    token = issue_jwt(user_id, "user", username)
    return ok({
        "user_id": user_id,
        "username": username,
        "registration_date": registration_date,
        "token": token,
    })
