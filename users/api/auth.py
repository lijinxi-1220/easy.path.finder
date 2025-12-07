from datetime import datetime, timedelta
import secrets
import jwt
from django.conf import settings
from .. import config
from .. import redis_client


def issue_jwt(user_id, role, username):
    secret = config.JWT_SECRET or settings.SECRET_KEY
    exp_seconds = int(config.JWT_EXP_SECONDS or 604800)
    jti = secrets.token_urlsafe(16)
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "username": username,
        "role": role,
        "jti": jti,
        "exp": datetime.utcnow() + timedelta(seconds=exp_seconds),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def auth_user_id(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    secret = config.JWT_SECRET or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None
    jti = payload.get("jti")
    if redis_client.redis and jti and redis_client.redis.get(f"jwt:blacklist:{jti}"):
        return None
    return payload.get("sub") or payload.get("user_id")


def blacklist_token(token):
    secret = config.JWT_SECRET or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return False, "token_expired"
    except Exception:
        return False, "invalid_token"
    jti = payload.get("jti")
    exp = payload.get("exp")
    if redis_client.redis and jti and exp:
        ttl = max(0, int(exp - datetime.utcnow().timestamp()))
        redis_client.redis.set(f"jwt:blacklist:{jti}", 1, ex=ttl)
    return True, None


def token_role(token):
    secret = config.JWT_SECRET or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("role")
    except Exception:
        return None


def resolve_user_id(request, provided_uid):
    uid = auth_user_id(request)
    if not provided_uid or provided_uid == uid:
        return uid
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
    role = token_role(token)
    if role == "admin":
        return provided_uid
    return None
