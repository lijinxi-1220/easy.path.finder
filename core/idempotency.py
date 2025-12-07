def ensure(redis, scope: str, key: str, ttl_seconds: int = 86400):
    if not redis or not key:
        return True
    id_key = f"idem:{scope}:{key}"
    existing = redis.get(id_key)
    if existing:
        return False
    redis.set(id_key, 1, ex=ttl_seconds)
    return True

