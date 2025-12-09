import json
import uuid
from datetime import datetime, UTC
from django.http import JsonResponse
from core.utils import ok, err
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..config import MODEL_PROVIDER
from chat.providers.mock import MockProvider
from ..repo import ChatRepo
from users.api.auth import auth_user_id
from core.exceptions import BusinessError, ErrorCode


def _session_list_key(uid):
    return ChatRepo.session_list_key(uid)


@csrf_exempt
@require_POST
def interact(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    uid = auth_user_id(request)
    content = body.get("message_content")
    scene = body.get("chat_scene") or "general"
    existing_chat_id = body.get("chat_id") or ""
    if not uid or not content:
        return err(ErrorCode.MISSING_PARAMS)
    ts = datetime.now(UTC).isoformat()
    if existing_chat_id:
        sess = ChatRepo.get_session(existing_chat_id) or {}
        if not sess or sess.get("user_id") != uid:
            return err(ErrorCode.SESSION_NOT_FOUND)
        chat_id = existing_chat_id
        ChatRepo.update_session_last_ts(chat_id, ts)
        ChatRepo.ensure_session_list_contains(uid, chat_id)
    else:
        chat_id = str(uuid.uuid4())
        ChatRepo.add_session(uid, chat_id, scene, ts)
    # store user message
    mid_u = str(uuid.uuid4())
    ChatRepo.append_message(chat_id, mid_u, "user", "message_content", content, ts)
    # context window (last 10 messages)
    histories = ChatRepo.list_messages(chat_id)
    msgs = []
    for mid in histories[-10:]:
        m = ChatRepo.get_message(mid) or {}
        if m:
            msgs.append({"role": m.get("role"), "content": m.get("message_content") or m.get("reply_content") or ""})
    provider = MockProvider() if MODEL_PROVIDER == "mock" else MockProvider()
    reply = provider.generate_reply(msgs + [{"role": "user", "content": content}], scene)
    mid_a = str(uuid.uuid4())
    ChatRepo.append_message(chat_id, mid_a, "assistant", "reply_content", reply, ts)
    return ok({"reply_content": reply, "timestamp": ts, "chat_id": chat_id})
