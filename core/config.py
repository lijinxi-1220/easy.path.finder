import os

from upstash_redis import Redis

UPSTASH_REDIS_REST_URL = "https://driven-warthog-45089.upstash.io"
UPSTASH_REDIS_REST_TOKEN = "AbAhAAIncDJmZWE1N2VlMmM4OTY0MGI4OGRiODY4ODdmNGYxYzNhN3AyNDUwODk"
JWT_SECRET = "user-secret"
JWT_EXP_SECONDS = 604800
SUBSCRIPTION_WEBHOOK_SECRET = "dev-webhook-secret"


def get(name: str, default: str = ""):
    return os.getenv(f"EASY_PATH_{name}", default)


def choose(module_value: str, env_name: str):
    env_val = os.getenv(f"EASY_PATH_{env_name}")
    return env_val if env_val else module_value


def is_debug():
    return os.getenv("EASY_PATH_DEBUG") == "1" or False


def get_redis():
    url = UPSTASH_REDIS_REST_URL
    token = UPSTASH_REDIS_REST_TOKEN
    if not url or not token:
        return None
    return Redis(url=url, token=token)
