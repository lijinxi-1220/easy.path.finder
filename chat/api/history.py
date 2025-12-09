from django.http import JsonResponse
from django.views.decorators.http import require_GET
from users.api.auth import auth_user_id
from core.utils import ok, err
from core.exceptions import BusinessError, ErrorCode
from ..repo import ChatRepo


@require_GET
def history(request):
    uid = auth_user_id(request)
    try:
        page = int(request.GET.get("page") or 1)
        page_size = int(request.GET.get("page_size") or 20)
    except ValueError:
        page, page_size = 1, 20
    ids = ChatRepo.list_session_ids(uid)
    if not ids:
        return err(ErrorCode.USER_NOT_FOUND_OR_NO_HISTORY)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    sessions = []
    for cid in ids[start:end]:
        msgs = ChatRepo.list_messages(cid)
        last_user = None
        last_assist = None
        for mid in msgs[::-1]:
            m = ChatRepo.get_message(mid) or {}
            if m.get("role") == "assistant" and not last_assist:
                last_assist = m
            if m.get("role") == "user" and not last_user:
                last_user = m
            if last_user and last_assist:
                break
        sessions.append({
            "chat_id": cid,
            "message_content": (last_user or {}).get("message_content", ""),
            "reply_content": (last_assist or {}).get("reply_content", ""),
            "timestamp": (last_assist or last_user or {}).get("timestamp", ""),
        })
    return ok({"chats": sessions, "meta": {"total": len(ids), "page": page, "page_size": page_size}})
