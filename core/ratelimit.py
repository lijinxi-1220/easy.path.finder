def allow(redis, key, limit, window_seconds):
    if not redis:
        return True
    try:
        val = redis.get(key)
        if val is None:
            redis.set(key, 1, ex=window_seconds)
            return True
        count = int(val)
        if count < limit:
            redis.set(key, count + 1, ex=window_seconds)
            return True
        return False
    except Exception:
        return True

