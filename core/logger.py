import json


SENSITIVE_KEYS = {"password", "token", "authorization", "payment_info"}


def _mask(value):
    if value is None:
        return None
    s = str(value)
    if len(s) <= 6:
        return "***"
    return s[:3] + "***" + s[-3:]


def sanitize(payload: dict):
    out = {}
    for k, v in payload.items():
        if k.lower() in SENSITIVE_KEYS:
            out[k] = _mask(v)
        else:
            out[k] = v
    return out


def log(level: str, **kwargs):
    try:
        print(json.dumps({"level": level, **sanitize(kwargs)}, ensure_ascii=False))
    except Exception:
        pass

