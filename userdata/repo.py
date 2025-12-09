from core import redis_client


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
    def get_user_by_id(uid):
        return redis_client.hgetall(f"user:id:{uid}") if redis_client.redis_client else {}

    @staticmethod
    def set_privacy(uid, mapping):
        redis_client.hset(UserDataRepo.privacy_key(uid), mapping=mapping)

    @staticmethod
    def get_privacy(uid):
        return redis_client.hgetall(UserDataRepo.privacy_key(uid)) if redis_client.redis_client else {}

    @staticmethod
    def list_history(uid):
        cur = redis_client.get(UserDataRepo.history_list_key(uid)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.hgetall(UserDataRepo.history_id_key(h)) for h in ids]
