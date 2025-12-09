import json
from datetime import datetime, timedelta, UTC
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from services.repo import ServicesRepo
from users.api.auth import auth_user_id
from core.utils import ok, err
from core.validators import validate_body
from core.exceptions import BusinessError, ErrorCode
from core.idempotency import ensure


@csrf_exempt
@require_POST
@validate_body({
    "props": {
        "subscription_type": {"type": "str", "required": True, "enum": {"month", "quarter", "year"}},
        "payment_info": {"type": "str"}
    }
})
def subscription(request):
    uid = auth_user_id(request)
    v = getattr(request, "validated_body", {})
    st = (v.get("subscription_type") or "").lower()
    payment_info = v.get("payment_info")
    if not uid:
        return err(ErrorCode.CREDENTIALS_ERROR)
    try:
        _ = json.dumps(payment_info or {})
    except Exception:
        return err(ErrorCode.PAYMENT_FAILED)
    idem = request.headers.get("Idempotency-Key")
    if not ensure(ServicesRepo.client(), "subscription", f"{uid}:{idem}" if idem else "", ttl_seconds=3600):
        return err(ErrorCode.MISSING_PARAMS)
    months = 1 if st == "month" else (3 if st == "quarter" else 12)
    expire = datetime.now(UTC) + timedelta(days=30 * months)
    status = "active"
    privileges = ["priority_support", "extra_recommendations"]
    ServicesRepo.update_subscription(uid, {
        "subscription_status": status,
        "expire_date": expire.isoformat(),
        "privileges": json.dumps(privileges),
    })
    return ok(ServicesRepo.get_subscription(uid) or {})
