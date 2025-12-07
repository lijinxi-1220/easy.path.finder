from . import redis_client


class ResumeRepo:
    @staticmethod
    def user_index_key(user_id):
        return f"resume:list:{user_id}"

    @staticmethod
    def id_key(resume_id):
        return f"resume:id:{resume_id}"

    @staticmethod
    def get(resume_id):
        return redis_client.redis.hgetall(ResumeRepo.id_key(resume_id)) if redis_client.redis else {}

    @staticmethod
    def list_by_user(user_id):
        cur = redis_client.redis.get(ResumeRepo.user_index_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.redis.hgetall(ResumeRepo.id_key(rid)) for rid in ids]

    @staticmethod
    def add_to_user(user_id, resume_id):
        cur = redis_client.redis.get(ResumeRepo.user_index_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        if resume_id not in ids:
            ids.append(resume_id)
        redis_client.redis.set(ResumeRepo.user_index_key(user_id), ",".join(ids))

    @staticmethod
    def update(resume_id, mapping):
        redis_client.redis.hset(ResumeRepo.id_key(resume_id), mapping=mapping)

