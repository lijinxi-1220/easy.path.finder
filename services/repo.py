from core import redis_client


class ServicesRepo:
    @staticmethod
    def client():
        return redis_client

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
    def consult_id_key(app_id):
        return f"consult:id:{app_id}"

    @staticmethod
    def consult_idx_key(uid, mentor_id, time_str):
        return f"consult:idx:{uid}:{mentor_id}:{time_str or ''}"

    @staticmethod
    def consult_rl_key(uid):
        return f"rl:consult:{uid}"

    @staticmethod
    def get_svc_ids(svc_type):
        cur = redis_client.get(ServicesRepo.svc_list_key(svc_type)) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def get_svc(svc_type, sid):
        return redis_client.hgetall(ServicesRepo.svc_id_key(svc_type, sid)) if redis_client.redis else {}

    @staticmethod
    def get_mentor_ids(field):
        cur = redis_client.get(ServicesRepo.mentor_list_key(field)) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def get_mentor(mid):
        return redis_client.hgetall(ServicesRepo.mentor_id_key(mid)) if redis_client.redis else {}

    @staticmethod
    def get_project_ids(pt):
        cur = redis_client.get(ServicesRepo.project_list_key(pt)) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def get_project(pid):
        return redis_client.hgetall(ServicesRepo.project_id_key(pid)) if redis_client.redis else {}

    @staticmethod
    def get_subscription(uid):
        return redis_client.hgetall(ServicesRepo.subscription_key(uid)) if redis_client.redis else {}

    @staticmethod
    def update_subscription(uid, mapping):
        redis_client.hset(ServicesRepo.subscription_key(uid), mapping=mapping)

    @staticmethod
    def get_consult(app_id):
        return redis_client.hgetall(ServicesRepo.consult_id_key(app_id)) if redis_client.redis else {}

    @staticmethod
    def create_consult(app_id, mapping):
        redis_client.hset(ServicesRepo.consult_id_key(app_id), mapping=mapping)

    @staticmethod
    def set_consult_idx(uid, mentor_id, time_str, app_id, ttl_seconds):
        redis_client.set(ServicesRepo.consult_idx_key(uid, mentor_id, time_str), app_id, ex=ttl_seconds)
