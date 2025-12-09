from functools import wraps
from datetime import datetime
from core.exceptions import BusinessError


def _cast(value, t):
    if t == "int":
        return int(value)
    if t == "str":
        return str(value)
    if t == "bool":
        s = str(value).strip().lower()
        if s in {"true", "1", "yes"}:
            return True
        if s in {"false", "0", "no"}:
            return False
        raise ValueError("invalid_bool")
    if t == "date":
        # expects YYYY-MM-DD, returns ISO date string
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    if t in {"iso-datetime", "datetime"}:
        s = str(value)
        s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s).isoformat()
    return value


def validate_query(config):
    """
    Generic query validator.
    config example:
    {
      "params": {
         "page": {"type":"int","default":1,"min":1},
         "page_size": {"type":"int","default":20,"min":1},
         "sort_by": {"type":"str","default":"name","enum":{"name","provider"}},
         "sort_order": {"type":"str","default":"asc","enum":{"asc","desc"}}
      }
    }
    Backward compatibility keys: page_default, page_size_default, sort_by_default, sort_order_default, sort_by_allowed
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            q = request.GET
            validated = {}
            params = config.get("params")
            if not params:
                # backward compatible path
                params = {
                    "page": {"type": "int", "default": config.get("page_default", 1), "min": 1},
                    "page_size": {"type": "int", "default": config.get("page_size_default", 20), "min": 1},
                    "sort_by": {"type": "str", "default": config.get("sort_by_default")},
                    "sort_order": {"type": "str", "default": config.get("sort_order_default", "asc"),
                                   "enum": {"asc", "desc"}},
                }
                allowed = config.get("sort_by_allowed")
                if allowed:
                    params["sort_by"]["enum"] = allowed
            for name, rule in params.items():
                raw = q.get(name)
                val = raw if raw is not None else rule.get("default")
                if rule.get("required") and val is None:
                    raise BusinessError(1002, "invalid_param", 400)
                if val is None:
                    validated[name] = None
                    continue
                try:
                    if rule.get("type"):
                        val = _cast(val, rule["type"])
                except Exception:
                    raise BusinessError(1002, "invalid_param", 400)
                if rule.get("min") is not None and isinstance(val, int) and val < rule["min"]:
                    raise BusinessError(1002, "invalid_param", 400)
                if rule.get("enum") and val not in rule["enum"]:
                    raise BusinessError(1002, "invalid_param", 400)
                validated[name] = val
            request.validated = validated
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def validate_body(config):
    """
    Validate JSON body. Example config:
    {
      "props": {
        "mentor_id": {"type":"str","required":true},
        "consult_topic": {"type":"str"},
        "consult_time": {"type":"iso-datetime"}
      }
    }
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            raw = request.body or b""
            try:
                import json
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                raise BusinessError(1002, "invalid_json", 400)
            validated = {}
            props = config.get("props", {})
            for name, rule in props.items():
                val = data.get(name)
                if val is None:
                    if rule.get("required"):
                        raise BusinessError(1002, "invalid_param", 400)
                    val = rule.get("default")
                if val is None:
                    validated[name] = None
                    continue
                try:
                    if rule.get("type"):
                        val = _cast(val, rule["type"])
                except Exception:
                    raise BusinessError(1002, "invalid_param", 400)
                if rule.get("enum") and val not in rule["enum"]:
                    raise BusinessError(1002, "invalid_param", 400)
                validated[name] = val
            request.validated_body = validated
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
