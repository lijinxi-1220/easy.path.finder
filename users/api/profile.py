import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from ..repo import UsersRepo
from .auth import auth_user_id, token_role
from django.conf import settings
from core.utils import ok, err


@csrf_exempt
@require_POST
def profile(request, user_id):
    authed_user_id = auth_user_id(request)
    if not authed_user_id:
        return err(ErrorCode.CREDENTIALS_ERROR)
    if authed_user_id != user_id:
        bearer = request.headers.get("Authorization", "")
        token = bearer.split(" ", 1)[1] if bearer.startswith("Bearer ") else ""
        role = token_role(token)
        if role != "admin":
            return err(ErrorCode.PERMISSION_DENIED)
    data = UsersRepo.get_by_id(user_id)
    if not data:
        return err(ErrorCode.USER_NOT_FOUND)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    allowed = {"full_name", "gender", "avatar_url"}
    update = {k: v for k, v in body.items() if k in allowed}
    if update:
        UsersRepo.update_fields(user_id, update)
    return ok(data)
