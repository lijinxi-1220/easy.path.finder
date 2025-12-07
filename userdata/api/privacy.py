import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from users import redis_client as users_rc
from userdata import redis_client
from userdata.repo import UserDataRepo
from users.api.auth import auth_user_id
from core.utils import ok, err


@csrf_exempt
def privacy(request):
    if request.method != "PUT":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    uid = auth_user_id(request)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    settings = body.get("privacy_settings")
    if not uid:
        return err(1002, "missing_params")
    user = users_rc.redis.hgetall(f"user:id:{uid}") if users_rc.redis else {}
    if not user:
        return err(1005, "user_not_found", status=404)
    # store json string
    try:
        settings_json = json.dumps(settings) if isinstance(settings, dict) else str(settings or "{}")
    except Exception:
        settings_json = "{}"
    UserDataRepo.set_privacy(uid, {
        "user_id": uid,
        "privacy_settings": settings_json,
        "status": "updated",
    })
    return ok(UserDataRepo.get_privacy(uid) or {})
