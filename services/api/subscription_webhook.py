from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from services import redis_client
from services.repo import ServicesRepo
from services.config import SUBSCRIPTION_WEBHOOK_SECRET
from core.security import verify_hmac
import json
from core.utils import ok
from core.exceptions import BusinessError


@csrf_exempt
def subscription_webhook(request):
    if request.method != "POST":
        raise BusinessError(405, "method_not_allowed", 405)
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    raw = request.body or b""
    sig = request.headers.get("X-Signature", "")
    if not verify_hmac(SUBSCRIPTION_WEBHOOK_SECRET, raw, sig):
        raise BusinessError(6006, "payment_failed", 400)
    try:
        event = json.loads(raw.decode("utf-8"))
    except Exception:
        raise BusinessError(6007, "invalid_params", 400)
    uid = event.get("user_id")
    status = event.get("status")
    if not uid or status not in {"active", "failed"}:
        raise BusinessError(6007, "invalid_params", 400)
    if status == "active":
        ServicesRepo.update_subscription(uid, {"subscription_status": "active"})
    else:
        ServicesRepo.update_subscription(uid, {"subscription_status": "failed"})
    return ok({"ok": True})
