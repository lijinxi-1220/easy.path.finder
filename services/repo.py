from . import redis_client


class ServicesRepo:
    @staticmethod
    def svc_list_key(svc_type):
        return f"svc:{svc_type}:list"

    @staticmethod
    def svc_id_key(svc_type, sid):
        return f"svc:{svc_type}:id:{sid}"

    @staticmethod
    def mentor_list_key(field):
        return f"mentor:list:{field}"

    @staticmethod
    def mentor_id_key(mid):
        return f"mentor:id:{mid}"

    @staticmethod
    def project_list_key(pt):
        return f"project:list:{pt}"

    @staticmethod
    def project_id_key(pid):
        return f"project:id:{pid}"

    @staticmethod
    def subscription_key(uid):
        return f"subscription:{uid}"

    @staticmethod
    def get_svc_ids(svc_type):
        cur = redis_client.redis.get(ServicesRepo.svc_list_key(svc_type)) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def get_svc(svc_type, sid):
        return redis_client.redis.hgetall(ServicesRepo.svc_id_key(svc_type, sid)) if redis_client.redis else {}

    @staticmethod
    def get_mentor_ids(field):
        cur = redis_client.redis.get(ServicesRepo.mentor_list_key(field)) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def get_mentor(mid):
        return redis_client.redis.hgetall(ServicesRepo.mentor_id_key(mid)) if redis_client.redis else {}

    @staticmethod
    def get_project_ids(pt):
        cur = redis_client.redis.get(ServicesRepo.project_list_key(pt)) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def get_project(pid):
        return redis_client.redis.hgetall(ServicesRepo.project_id_key(pid)) if redis_client.redis else {}

    @staticmethod
    def get_subscription(uid):
        return redis_client.redis.hgetall(ServicesRepo.subscription_key(uid)) if redis_client.redis else {}

    @staticmethod
    def update_subscription(uid, mapping):
        redis_client.redis.hset(ServicesRepo.subscription_key(uid), mapping=mapping)

