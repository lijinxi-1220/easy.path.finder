import uuid

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.idempotency import ensure
from core.ratelimit import allow
from core.utils import ok, err
from core.validators import validate_body
from services.repo import ServicesRepo
from users.api.auth import auth_user_id


@csrf_exempt
@validate_body({
    "props": {
        "mentor_id": {"type": "str", "required": True},
        "consult_topic": {"type": "str"},
        "consult_time": {"type": "iso-datetime"},
    }
})
@require_POST
def consult(request):
    uid = auth_user_id(request)
    v = getattr(request, "validated_body", {})
    mentor_id = v.get("mentor_id")
    topic = v.get("consult_topic")
    time = v.get("consult_time")
    if not uid or not mentor_id:
        return err(ErrorCode.CREDENTIALS_ERROR)
    # rate-limit per user
    if not allow(ServicesRepo.client(), ServicesRepo.consult_rl_key(uid), limit=3, window_seconds=3600):
        return err(ErrorCode.RATE_LIMIT)
    m = ServicesRepo.get_mentor(mentor_id) or {}
    if not m:
        return err(ErrorCode.MENTOR_NOT_FOUND)
    # prevent duplicate by user+mentor+time
    idx_key = ServicesRepo.consult_idx_key(uid, mentor_id, time)
    if ServicesRepo.client().get(idx_key):
        return err(ErrorCode.CREDENTIALS_ERROR)
    idem = request.headers.get("Idempotency-Key")
    if not ensure(ServicesRepo.client(), "consult", f"{uid}:{idem}" if idem else "", ttl_seconds=3600):
        return err(ErrorCode.CREDENTIALS_ERROR)
    app_id = str(uuid.uuid4())
    ServicesRepo.create_consult(app_id, mapping={
        "application_id": app_id,
        "user_id": uid,
        "mentor_id": mentor_id,
        "consult_topic": topic or "",
        "consult_time": time or "",
        "application_status": "submitted",
        "feedback": "",
    })
    ServicesRepo.set_consult_idx(uid, mentor_id, time, app_id, ttl_seconds=3600)
    return ok(ServicesRepo.get_consult(app_id) or {})
