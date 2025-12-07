from . import redis_client


class MatchesRepo:
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
    def get_job_profile_id(title: str, industry: str):
        return redis_client.redis.get(MatchesRepo.job_index_key(title, industry)) if redis_client.redis else None

    @staticmethod
    def get_job_profile(pid: str):
        return redis_client.redis.hgetall(MatchesRepo.job_id_key(pid)) if redis_client.redis else {}

    @staticmethod
    def get_school(sid: str):
        return redis_client.redis.hgetall(MatchesRepo.school_id_key(sid)) if redis_client.redis else {}

