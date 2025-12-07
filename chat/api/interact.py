import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from core.utils import ok, err
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from ..config import MODEL_PROVIDER
from chat.providers.mock import MockProvider
from ..repo import ChatRepo
from users.api.auth import auth_user_id


def _session_list_key(uid):
    return f"chat:session:list:{uid}"


@csrf_exempt
def interact(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return err(1002, "invalid_json")
    uid = auth_user_id(request)
    content = body.get("message_content")
    scene = body.get("chat_scene") or "general"
    existing_chat_id = body.get("chat_id") or ""
    if not uid or not content:
        return err(1002, "missing_params")
    ts = datetime.utcnow().isoformat()
    if existing_chat_id:
        sess = ChatRepo.get_session(existing_chat_id) or {}
        if not sess or sess.get("user_id") != uid:
            return err(5001, "session_not_found", status=404)
        chat_id = existing_chat_id
        ChatRepo.update_session_last_ts(chat_id, ts)
        # ensure listed
        cur = redis_client.redis.get(ChatRepo.session_list_key(uid)) or ""
        ids = [x for x in cur.split(",") if x]
        if chat_id not in ids:
            redis_client.redis.set(ChatRepo.session_list_key(uid), ",".join(ids + [chat_id]))
    else:
        chat_id = str(uuid.uuid4())
        ChatRepo.add_session(uid, chat_id, scene, ts)
    # store user message
    mid_u = str(uuid.uuid4())
    ChatRepo.append_message(chat_id, mid_u, "user", "message_content", content, ts)
    # context window (last 10 messages)
    histories = (redis_client.redis.get(f"chat:messages:list:{chat_id}") or "").split(",")
    msgs = []
    for mid in histories[-10:]:
        m = redis_client.redis.hgetall(f"chat:message:{mid}") or {}
        if m:
            msgs.append({"role": m.get("role"), "content": m.get("message_content") or m.get("reply_content") or ""})
    provider = MockProvider() if MODEL_PROVIDER == "mock" else MockProvider()
    reply = provider.generate_reply(msgs + [{"role": "user", "content": content}], scene)
    mid_a = str(uuid.uuid4())
    ChatRepo.append_message(chat_id, mid_a, "assistant", "reply_content", reply, ts)
    return ok({"reply_content": reply, "timestamp": ts, "chat_id": chat_id})
