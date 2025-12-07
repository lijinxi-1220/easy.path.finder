from upstash_redis import Redis
from . import config


def get_redis():
    url = config.CHAT_REDIS_REST_URL
    token = config.CHAT_REDIS_REST_TOKEN
    if not url or not token:
        return None
    return Redis(url=url, token=token)


redis = get_redis()

