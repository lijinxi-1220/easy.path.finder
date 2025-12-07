from . import redis_client


class UsersRepo:
    @staticmethod
    def id_key(user_id: str):
        return f"user:id:{user_id}"

    @staticmethod
    def username_key(username: str):
        return f"user:username:{username}"

    @staticmethod
    def email_key(email: str):
        return f"user:email:{email}"

    @staticmethod
    def phone_key(phone: str):
        return f"user:phone:{phone}"

    @staticmethod
    def get_by_id(user_id: str):
        return redis_client.redis.hgetall(UsersRepo.id_key(user_id)) if redis_client.redis else {}

    @staticmethod
    def get_user_id_by_username(username: str):
        return redis_client.redis.get(UsersRepo.username_key(username)) if redis_client.redis else None

    @staticmethod
    def get_user_id_by_email(email: str):
        return redis_client.redis.get(UsersRepo.email_key(email)) if redis_client.redis else None

    @staticmethod
    def get_user_id_by_phone(phone: str):
        return redis_client.redis.get(UsersRepo.phone_key(phone)) if redis_client.redis else None

    @staticmethod
    def update(user_id: str, mapping: dict):
        redis_client.redis.hset(UsersRepo.id_key(user_id), mapping=mapping)

