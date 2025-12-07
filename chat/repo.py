from . import redis_client


class ChatRepo:
    @staticmethod
    def session_list_key(uid):
        return f"chat:session:list:{uid}"

    @staticmethod
    def session_key(cid):
        return f"chat:session:{cid}"

    @staticmethod
    def msg_list_key(cid):
        return f"chat:messages:list:{cid}"

    @staticmethod
    def msg_key(mid):
        return f"chat:message:{mid}"

    @staticmethod
    def add_session(uid, cid, scene, created_at):
        redis_client.redis.hset(ChatRepo.session_key(cid), mapping={
            "chat_id": cid,
            "user_id": uid,
            "chat_scene": scene,
            "created_at": created_at,
            "last_ts": created_at,
        })
        cur = redis_client.redis.get(ChatRepo.session_list_key(uid)) or ""
        ids = [x for x in cur.split(",") if x]
        if cid not in ids:
            ids.append(cid)
        redis_client.redis.set(ChatRepo.session_list_key(uid), ",".join(ids))

    @staticmethod
    def update_session_last_ts(cid, ts):
        redis_client.redis.hset(ChatRepo.session_key(cid), mapping={"last_ts": ts})

    @staticmethod
    def get_session(cid):
        return redis_client.redis.hgetall(ChatRepo.session_key(cid)) if redis_client.redis else {}

    @staticmethod
    def append_message(cid, mid, role, content_field, content, ts):
        mapping = {
            "message_id": mid,
            "chat_id": cid,
            "role": role,
            content_field: content,
            "timestamp": ts,
        }
        redis_client.redis.hset(ChatRepo.msg_key(mid), mapping=mapping)
        cur = redis_client.redis.get(ChatRepo.msg_list_key(cid)) or ""
        redis_client.redis.set(ChatRepo.msg_list_key(cid), cur + ("," if cur else "") + mid)

    @staticmethod
    def list_messages(cid):
        mids = (redis_client.redis.get(ChatRepo.msg_list_key(cid)) or "").split(",")
        return [m for m in mids if m]

