from django.views.decorators.http import require_GET

from core.exceptions import ErrorCode
from core.utils import ok, err
from userdata.repo import UserDataRepo
from users.api.auth import auth_user_id


@require_GET
def history(request):
    uid = auth_user_id(request)
    if not uid:
        return err(ErrorCode.MISSING_PARAMS)
    # time_range format: startISO,endISO
    tr = (request.GET.get("time_range") or "").split(",")
    start = tr[0] if len(tr) > 0 and tr[0] else ""
    end = tr[1] if len(tr) > 1 and tr[1] else ""
    entries = UserDataRepo.list_history(uid)
    if not entries:
        return err(ErrorCode.USER_NOT_FOUND_OR_NO_HISTORY)
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
