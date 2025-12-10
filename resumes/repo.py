from core import redis_client


class ResumeRepo:
    @staticmethod
    def client():
        return redis_client
    @staticmethod
    def user_index_key(user_id):
        return f"resume:list:{user_id}"

    @staticmethod
    def id_key(resume_id):
        return f"resume:id:{resume_id}"

    @staticmethod
    def get(resume_id):
        return redis_client.hgetall(ResumeRepo.id_key(resume_id)) if redis_client else {}

    @staticmethod
    def list_by_user(user_id):
        cur = redis_client.get(ResumeRepo.user_index_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.hgetall(ResumeRepo.id_key(rid)) for rid in ids] if redis_client else []

    @staticmethod
    def add_to_user(user_id, resume_id):
        cur = redis_client.get(ResumeRepo.user_index_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        if resume_id not in ids:
            ids.append(resume_id)
        redis_client.set(ResumeRepo.user_index_key(user_id), ",".join(ids))

    @staticmethod
    def update(resume_id, mapping):
        redis_client.hset(ResumeRepo.id_key(resume_id), values=mapping) if redis_client else None

    @staticmethod
    def create(resume_id, mapping):
        redis_client.hset(ResumeRepo.id_key(resume_id), values=mapping) if redis_client else None

    @staticmethod
    def set_user_list(user_id, ids):
        redis_client.set(ResumeRepo.user_index_key(user_id), ",".join(ids)) if redis_client else None
