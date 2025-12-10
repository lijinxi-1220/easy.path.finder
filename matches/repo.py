from core import redis_client


class MatchesRepo:
    @staticmethod
    def client():
        return redis_client

    @staticmethod
    def job_index_key(title: str, industry: str):
        return f"job:profile:index:{title}:{industry}"

    @staticmethod
    def job_id_key(pid: str):
        return f"job:profile:{pid}"

    @staticmethod
    def school_id_key(sid: str):
        return f"school:id:{sid}"

    @staticmethod
    def job_list_key():
        return "job:profile:list"

    @staticmethod
    def school_list_key():
        return "school:list"

    @staticmethod
    def school_index_key(slug: str):
        return f"school:index:{slug}"

    @staticmethod
    def match_id_key(mid: str):
        return f"match:id:{mid}"

    @staticmethod
    def get_job_profile_id(title: str, industry: str):
        return redis_client.get(MatchesRepo.job_index_key(title, industry)) if redis_client else None

    @staticmethod
    def get_job_profile(pid: str):
        return redis_client.hgetall(MatchesRepo.job_id_key(pid)) if redis_client else {}

    @staticmethod
    def get_school(sid: str):
        return redis_client.hgetall(MatchesRepo.school_id_key(sid)) if redis_client else {}

    @staticmethod
    def get_job_ids():
        cur = redis_client.get(MatchesRepo.job_list_key()) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def get_school_ids():
        cur = redis_client.get(MatchesRepo.school_list_key()) or ""
        return [x for x in cur.split(",") if x]

    @staticmethod
    def set_job_profile(pid: str, mapping: dict):
        redis_client.hset(MatchesRepo.job_id_key(pid), values=mapping)

    @staticmethod
    def set_job_index(title: str, industry: str, pid: str):
        redis_client.set(MatchesRepo.job_index_key(title, industry), pid)

    @staticmethod
    def add_job_to_list(pid: str):
        cur = redis_client.get(MatchesRepo.job_list_key()) or ""
        ids = [x for x in cur.split(",") if x]
        if pid not in ids:
            ids.append(pid)
        redis_client.set(MatchesRepo.job_list_key(), ",".join(ids))

    @staticmethod
    def set_school(sid: str, mapping: dict):
        redis_client.hset(MatchesRepo.school_id_key(sid), values=mapping)

    @staticmethod
    def set_school_index(slug: str, sid: str):
        redis_client.set(MatchesRepo.school_index_key(slug), sid)

    @staticmethod
    def add_school_to_list(sid: str):
        cur = redis_client.get(MatchesRepo.school_list_key()) or ""
        ids = [x for x in cur.split(",") if x]
        if sid not in ids:
            ids.append(sid)
        redis_client.set(MatchesRepo.school_list_key(), ",".join(ids))

    @staticmethod
    def create_match(mid: str, mapping: dict):
        redis_client.hset(MatchesRepo.match_id_key(mid), values=mapping)

    @staticmethod
    def get_match(mid: str):
        return redis_client.hgetall(MatchesRepo.match_id_key(mid)) if redis_client else {}
