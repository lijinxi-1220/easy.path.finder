import json
import uuid
from datetime import datetime, UTC

from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import BusinessError, ErrorCode
from core.utils import ok, err
from .auth import issue_jwt
from ..repo import UsersRepo


@csrf_exempt
@require_POST
def register(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    username = (data.get("username") or "").strip()
    password = data.get("password")
    email = data.get("email")
    phone = data.get("phone_number")
    if not username or not password:
        return err(ErrorCode.MISSING_PARAMS)
    if UsersRepo.exists_username(username):
        return err(ErrorCode.USERNAME_EXISTS)
    idem = request.headers.get("Idempotency-Key")
    from core.idempotency import ensure as _ensure
    if not _ensure(UsersRepo.client(), "register", f"{username}:{idem}" if idem else "", ttl_seconds=3600):
        return err(ErrorCode.REQUEST_ERROR)
    user_id = str(uuid.uuid4())
    registration_date = datetime.now(UTC).isoformat()
    password_hash = make_password(password)
    UsersRepo.set_username_index(username, user_id)
    if email:
        UsersRepo.set_email_index(email, user_id)
    if phone:
        UsersRepo.set_phone_index(phone, user_id)
    UsersRepo.create_user(
        user_id,
        mapping={
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "email": email or "",
            "phone_number": phone or "",
            "registration_date": registration_date,
            "last_login_date": "",
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
