import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from services import redis_client
from services.repo import ServicesRepo
from users.api.auth import auth_user_id
from core.utils import ok
from core.validators import validate_body
from core.exceptions import BusinessError
from core.idempotency import ensure


@csrf_exempt
@validate_body({
    "props": {
        "subscription_type": {"type": "str", "required": True, "enum": {"month", "quarter", "year"}},
        "payment_info": {"type": "str"}
    }
})
def subscription(request):
    if request.method != "POST":
        raise BusinessError(405, "method_not_allowed", 405)
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    uid = auth_user_id(request)
    v = getattr(request, "validated_body", {})
    st = (v.get("subscription_type") or "").lower()
    payment_info = v.get("payment_info")
    if not uid:
        raise BusinessError(6007, "invalid_params", 400)
    try:
        _ = json.dumps(payment_info or {})
    except Exception:
        raise BusinessError(6006, "payment_failed", 400)
    idem = request.headers.get("Idempotency-Key")
    if not ensure(redis_client.redis, "subscription", f"{uid}:{idem}" if idem else "", ttl_seconds=3600):
        raise BusinessError(6007, "invalid_params", 400)
    months = 1 if st == "month" else (3 if st == "quarter" else 12)
    expire = datetime.utcnow() + timedelta(days=30 * months)
    status = "active"
    privileges = ["priority_support", "extra_recommendations"]
    ServicesRepo.update_subscription(uid, {
        "subscription_status": status,
        "expire_date": expire.isoformat(),
        "privileges": json.dumps(privileges),
    })
    return ok(ServicesRepo.get_subscription(uid) or {})
