import json
import secrets
from datetime import datetime, UTC

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.ratelimit import allow
from core.utils import ok, err
from .auth import issue_jwt
from ..repo import UsersRepo


@csrf_exempt
@require_POST
def send_code(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    email = (body.get("email") or "").strip()
    phone = str(body.get("phone_number") or "").strip()
    if not email and not phone:
        return err(ErrorCode.MISSING_PARAMS)
    if email:
        otp_key = UsersRepo.otp_email_key(email)
        user_index_key = UsersRepo.email_key(email)
        user_id = UsersRepo.get_user_id_by_email(email)
    else:
        otp_key = UsersRepo.otp_phone_key(phone)
        user_index_key = UsersRepo.phone_key(phone)
        user_id = UsersRepo.get_user_id_by_phone(phone)
    if not user_id:
        return err(ErrorCode.USER_NOT_FOUND)
    rl_key = UsersRepo.otp_rl_key(user_index_key)
    if UsersRepo.get_otp(rl_key):
        return err(ErrorCode.RATE_LIMIT)
    # global rate limit per IP
    ip = request.META.get("REMOTE_ADDR", "unknown")
    if not allow(UsersRepo.client(), UsersRepo.otp_rate_limit_key(ip), limit=5, window_seconds=60):
        return err(ErrorCode.RATE_LIMIT)
    code = f"{secrets.randbelow(1000000):06d}"
    UsersRepo.set_otp(otp_key, code, ttl_seconds=300)
    UsersRepo.set_otp(rl_key, "1", ttl_seconds=60)
    return ok({"code": code})


@csrf_exempt
@require_POST
def login_code(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    email = (body.get("email") or "").strip()
    phone = str(body.get("phone_number") or "").strip()
    code = (body.get("code") or "").strip()
    if not code or (not email and not phone):
        return err(ErrorCode.MISSING_PARAMS)
    if email:
        otp_key = UsersRepo.otp_email_key(email)
        expect = UsersRepo.get_otp(otp_key)
    else:
        otp_key = UsersRepo.otp_phone_key(phone)
        expect = UsersRepo.get_otp(otp_key)
    if not expect or expect != code:
        return err(ErrorCode.REQUEST_ERROR)
    user_id = UsersRepo.get_user_id_by_email(email) if email else UsersRepo.get_user_id_by_phone(phone)
    if not user_id:
        return err(ErrorCode.USER_NOT_FOUND)
    user = UsersRepo.get_by_id(user_id) or {}
    token = issue_jwt(user_id, user.get("role", "user"), user.get("username", email or phone))
    UsersRepo.delete_otp(otp_key)
    last_login_date = datetime.now(UTC).isoformat()
    UsersRepo.update_last_login_date(user_id, last_login_date)
    return ok({
        "user_id": user_id,
        "token": token,
        "last_login_date": last_login_date,
    })
