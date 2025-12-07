import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from ..repo import UsersRepo
from .auth import auth_user_id, token_role
from django.conf import settings
from core.utils import ok, err


@csrf_exempt
def profile(request, user_id):
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    authed_user_id = auth_user_id(request)
    if not authed_user_id:
        return err(1010, "invalid_token", status=401)
    if authed_user_id != user_id:
        bearer = request.headers.get("Authorization", "")
        token = bearer.split(" ", 1)[1] if bearer.startswith("Bearer ") else ""
        role = token_role(token)
        if role != "admin":
            return err(1006, "permission_denied", status=403)
    key = f"user:id:{user_id}"
    if request.method == "GET":
        data = UsersRepo.get_by_id(user_id)
        if not data:
            return err(1005, "user_not_found", status=404)
        return ok(data)
    if request.method in ("POST", "PUT"):
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            return err(1002, "invalid_json")
        allowed = {"full_name", "gender", "avatar_url"}
        update = {k: v for k, v in body.items() if k in allowed}
        if update:
            redis_client.redis.hset(key, mapping=update)
        data = UsersRepo.get_by_id(user_id)
        if not data:
            return err(1005, "user_not_found", status=404)
        return ok(data)
    return err(405, "method_not_allowed", status=405)
