import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from userdata.repo import UserDataRepo
from users.api.auth import auth_user_id
from core.utils import ok, err


@csrf_exempt
@require_POST
def privacy(request):
    uid = auth_user_id(request)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    settings = body.get("privacy_settings")
    if not uid:
        return err(ErrorCode.USER_NOT_FOUND)
    user = UserDataRepo.get_user_by_id(uid)
    if not user:
        return err(ErrorCode.USER_NOT_FOUND)
    # store json string
    settings_json = json.dumps(settings) if isinstance(settings, dict) else str(settings or "{}")
    UserDataRepo.set_privacy(uid, {
        "user_id": uid,
        "privacy_settings": settings_json,
        "status": "updated",
    })
    return ok(UserDataRepo.get_privacy(uid) or {})
