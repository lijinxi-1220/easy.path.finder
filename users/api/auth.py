from datetime import datetime, timedelta, UTC
import secrets
import jwt
from django.conf import settings
from core import config
from ..repo import UsersRepo

type JWTError = jwt.ExpiredSignatureError | jwt.InvalidTokenError | jwt.InvalidSignatureError


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
        "exp": datetime.now(UTC) + timedelta(seconds=exp_seconds),
        "iat": datetime.now(UTC),
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
    except JWTError:
        return None
    jti = payload.get("jti")
    if UsersRepo.client() and jti and UsersRepo.jwt_blacklist_exists(jti):
        return None
    return payload.get("sub") or payload.get("user_id")


def blacklist_token(token):
    secret = config.JWT_SECRET or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        return False, "toke expired or invalid"
    jti = payload.get("jti")
    exp = payload.get("exp")
    if UsersRepo.client() and jti and exp:
        ttl = max(0, int(exp - datetime.now(UTC).timestamp()))
        UsersRepo.jwt_blacklist_add(jti, ttl)
    return True, None


def token_role(token):
    secret = config.JWT_SECRET or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("role")
    except JWTError:
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
