from . import redis_client


class UserDataRepo:
    @staticmethod
    def privacy_key(uid):
        return f"user:privacy:{uid}"

    @staticmethod
    def history_list_key(uid):
        return f"user:history:list:{uid}"

    @staticmethod
    def history_id_key(hid):
        return f"user:history:id:{hid}"

    @staticmethod
    def set_privacy(uid, mapping):
        redis_client.redis.hset(UserDataRepo.privacy_key(uid), mapping=mapping)

    @staticmethod
    def get_privacy(uid):
        return redis_client.redis.hgetall(UserDataRepo.privacy_key(uid)) if redis_client.redis else {}

    @staticmethod
    def list_history(uid):
        cur = redis_client.redis.get(UserDataRepo.history_list_key(uid)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.redis.hgetall(UserDataRepo.history_id_key(h)) for h in ids]

