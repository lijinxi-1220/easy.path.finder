from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from services.repo import ServicesRepo
from services.config import SUBSCRIPTION_WEBHOOK_SECRET
from core.security import verify_hmac
import json
from core.utils import ok, err
from core.exceptions import BusinessError, ErrorCode


@csrf_exempt
@require_POST
def subscription_webhook(request):
    raw = request.body or b""
    sig = request.headers.get("X-Signature", "")
    if not verify_hmac(SUBSCRIPTION_WEBHOOK_SECRET, raw, sig):
        return err(ErrorCode.CREDENTIALS_ERROR)
    try:
        event = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    uid = event.get("user_id")
    status = event.get("status")
    if not uid or status not in {"active", "failed"}:
        return err(ErrorCode.REQUEST_ERROR)
    if status == "active":
        ServicesRepo.update_subscription(uid, {"subscription_status": "active"})
    else:
        ServicesRepo.update_subscription(uid, {"subscription_status": "failed"})
    return ok({"ok": True})
