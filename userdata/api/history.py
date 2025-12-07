from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from users.api.auth import auth_user_id
from userdata import redis_client
from userdata.repo import UserDataRepo
from core.utils import ok
from core.exceptions import BusinessError


@require_GET
def history(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    uid = auth_user_id(request)
    if not uid:
        raise BusinessError(1002, "missing_params", 400)
    # time_range format: startISO,endISO
    tr = (request.GET.get("time_range") or "").split(",")
    start = tr[0] if len(tr) > 0 and tr[0] else ""
    end = tr[1] if len(tr) > 1 and tr[1] else ""
    entries = UserDataRepo.list_history(uid)
    if not entries:
        raise BusinessError(1005, "user_not_found_or_no_history", 404)
    items = []
    for h in entries:
        if not h:
            continue
        ts = h.get("timestamp", "")
        if start and ts < start:
            continue
        if end and ts > end:
            continue
        items.append(h)
    return ok({"history": items})
