import json
from datetime import datetime, UTC

from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.ratelimit import allow
from core.utils import ok, err
from .auth import issue_jwt
from ..repo import UsersRepo


@csrf_exempt
@require_POST
def login(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    phone = str(data.get("phone_number") or "").strip()
    password = data.get("password")
    if not password or (not username and not email and not phone):
        return err(ErrorCode.MISSING_PARAMS)
    # rate limit per IP
    ip = request.META.get("REMOTE_ADDR", "unknown")
    if not allow(UsersRepo.client(), UsersRepo.login_rate_limit_key(ip), limit=10, window_seconds=60):
        return err(ErrorCode.RATE_LIMIT)
    user_id = None
    if username:
        user_id = UsersRepo.get_user_id_by_username(username)
    elif email:
        user_id = UsersRepo.get_user_id_by_email(email)
    elif phone:
        user_id = UsersRepo.get_user_id_by_phone(phone)
    if not user_id:
        return err(ErrorCode.CREDENTIALS_ERROR)
    user = UsersRepo.get_by_id(user_id)
    if not user:
        return err(ErrorCode.CREDENTIALS_ERROR)
    if not check_password(password, user.get("password_hash", "")):
        return err(ErrorCode.CREDENTIALS_ERROR)
    last_login_date = datetime.now(UTC).isoformat()
    UsersRepo.update_last_login_date(user_id, last_login_date)
    token = issue_jwt(user_id, user.get("role", "user"), user.get("username", username or email or phone))
    return ok({
        "user_id": user_id,
        "token": token,
        "last_login_date": last_login_date
    })
