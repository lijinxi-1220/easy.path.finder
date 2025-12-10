from core import redis_client


class UsersRepo:
    @staticmethod
    def client():
        return redis_client

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
    def otp_rate_limit_key(ip: str):
        return f"rl:otp:{ip}"

    @staticmethod
    def jwt_blacklist_key(jti: str):
        return f"jwt:blacklist:{jti}"

    @staticmethod
    def otp_email_key(email: str):
        return f"otp:email:{email}"

    @staticmethod
    def otp_phone_key(phone: str):
        return f"otp:phone:{phone}"

    @staticmethod
    def otp_rl_key(user_index_key: str):
        return f"otp:rl:{user_index_key}"

    @staticmethod
    def get_by_id(user_id: str):
        return redis_client.hgetall(UsersRepo.id_key(user_id)) if redis_client else {}

    @staticmethod
    def get_user_id_by_username(username: str):
        return redis_client.get(UsersRepo.username_key(username)) if redis_client else None

    @staticmethod
    def get_user_id_by_email(email: str):
        return redis_client.get(UsersRepo.email_key(email)) if redis_client else None

    @staticmethod
    def get_user_id_by_phone(phone: str):
        return redis_client.get(UsersRepo.phone_key(phone)) if redis_client else None

    @staticmethod
    def update(user_id: str, mapping: dict):
        redis_client.hset(UsersRepo.id_key(user_id), values=mapping)

    @staticmethod
    def create_user(user_id: str, mapping: dict):
        redis_client.hset(UsersRepo.id_key(user_id),values=mapping)

    @staticmethod
    def update_fields(user_id: str, mapping: dict):
        redis_client.hset(UsersRepo.id_key(user_id), values=mapping)

    @staticmethod
    def update_last_login_date(user_id: str, last_login_date: str):
        redis_client.hset(UsersRepo.id_key(user_id), values={"last_login_date": last_login_date})

    @staticmethod
    def exists_username(username: str):
        return redis_client.exists(UsersRepo.username_key(username)) if redis_client else 0

    @staticmethod
    def set_username_index(username: str, user_id: str):
        redis_client.set(UsersRepo.username_key(username), user_id)

    @staticmethod
    def set_email_index(email: str, user_id: str):
        redis_client.set(UsersRepo.email_key(email), user_id)

    @staticmethod
    def set_phone_index(phone: str, user_id: str):
        redis_client.set(UsersRepo.phone_key(phone), user_id)

    @staticmethod
    def get_otp(key: str):
        return redis_client.get(key) if redis_client else None

    @staticmethod
    def set_otp(key: str, code: str, ttl_seconds: int):
        redis_client.set(key, code, ex=ttl_seconds)

    @staticmethod
    def delete_otp(key: str):
        redis_client.delete(key)

    @staticmethod
    def jwt_blacklist_exists(jti: str):
        return redis_client.get(UsersRepo.jwt_blacklist_key(jti)) if redis_client else None

    @staticmethod
    def jwt_blacklist_add(jti: str, ttl_seconds: int):
        redis_client.set(UsersRepo.jwt_blacklist_key(jti), 1, ex=ttl_seconds)

    @staticmethod
    def login_rate_limit_key(ip: str):
        return f"rl:login:{ip}"
