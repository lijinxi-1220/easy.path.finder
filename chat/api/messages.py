from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..repo import ChatRepo
from users.api.auth import auth_user_id
from core.utils import ok, err, get_pagination_params
from core.exceptions import BusinessError, ErrorCode


@require_GET
def messages(request):
    uid = auth_user_id(request)
    chat_id = request.GET.get("chat_id") or ""
    if not uid or not chat_id:
        return err(ErrorCode.MISSING_PARAMS)
    # basic ownership check
    sess = ChatRepo.get_session(chat_id) or {}
    if not sess or sess.get("user_id") != uid:
        return err(ErrorCode.USER_NOT_FOUND_OR_NO_HISTORY)
    page, page_size = get_pagination_params(request)
    mids = ChatRepo.list_messages(chat_id)
    total = len(mids)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    items = []
    for mid in mids[start:end]:
        m = ChatRepo.get_message(mid) or {}
        if m:
            items.append({
                "message_id": m.get("message_id"),
                "role": m.get("role"),
                "message_content": m.get("message_content"),
                "reply_content": m.get("reply_content"),
                "timestamp": m.get("timestamp"),
            })
    return ok({"messages": items, "meta": {"total": total, "page": page, "page_size": page_size}})
