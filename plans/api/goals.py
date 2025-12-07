import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from users.api.auth import auth_user_id
from core.utils import ok
from core.validators import validate_query
from core.exceptions import BusinessError


def _list_key(user_id):
    return f"plan:goal:list:{user_id}"


@csrf_exempt
def goals(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)

    if request.method == "GET":
        uid = auth_user_id(request)
        gid = request.GET.get("goal_id") or ""
        if gid:
            data = redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {}
            if not data or data.get("user_id") != uid:
                return err(4001, "goal_not_found", status=404)
            return ok(data)
        cur = redis_client.redis.get(_list_key(uid)) or ""
        ids = [x for x in cur.split(",") if x]
        items = []
        for g in ids:
            d = redis_client.redis.hgetall(f"plan:goal:id:{g}") or {}
            if d:
                items.append({
                    "goal_id": d.get("goal_id"),
                    "goal_name": d.get("goal_name"),
                    "status": d.get("status", "active"),
                    "target_date": d.get("target_date", ""),
                    "created_at": d.get("created_at", ""),
                })
        # filters
        status = (request.GET.get("status") or "").strip()
        q = (request.GET.get("q") or "").strip().lower()
        due_from = request.GET.get("due_from") or ""
        due_to = request.GET.get("due_to") or ""
        if status:
            items = [it for it in items if (it.get("status") or "") == status]
        if q:
            items = [it for it in items if q in (it.get("goal_name") or "").lower()]
        if due_from:
            items = [it for it in items if (it.get("target_date") or "") >= due_from]
        if due_to:
            items = [it for it in items if (it.get("target_date") or "") <= due_to]
        # sort + pagination via validator
        # apply validator
        from core.validators import validate_query as _v
        @(_v({
            "params": {
                "sort_by": {"type": "str", "default": "created_at", "enum": {"created_at", "target_date", "goal_name", "status"}},
                "sort_order": {"type": "str", "default": "desc", "enum": {"asc", "desc"}},
                "page": {"type": "int", "default": 1, "min": 1},
                "page_size": {"type": "int", "default": 20, "min": 1},
            }
        }))
        def _apply(req):
            return req
        _apply(request)
        v = getattr(request, "validated", {})
        sort_by = v["sort_by"]
        sort_order = v["sort_order"]
        items.sort(key=lambda x: x.get(sort_by) or "", reverse=(sort_order == "desc"))
        # pagination
        page = v["page"]
        page_size = v["page_size"]
        total = len(items)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return ok({"goals": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}})

    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            raise BusinessError(1002, "invalid_json", 400)
        uid = auth_user_id(request)
        goal_name = body.get("goal_name")
        desc = body.get("description") or ""
        target_date = body.get("target_date") or ""
        if not uid or not goal_name:
            raise BusinessError(1002, "missing_params", 400)
        gid = str(uuid.uuid4())
        redis_client.redis.hset(f"plan:goal:id:{gid}", mapping={
            "goal_id": gid,
            "user_id": uid,
            "goal_name": goal_name,
            "description": desc,
            "target_date": target_date,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        })
        cur = redis_client.redis.get(_list_key(uid)) or ""
        ids = [x for x in cur.split(",") if x] + [gid]
        redis_client.redis.set(_list_key(uid), ",".join(ids))
        return ok(redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {})

    if request.method == "PUT":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            raise BusinessError(1002, "invalid_json", 400)
        uid = auth_user_id(request)
        gid = body.get("goal_id")
        if not gid:
            return JsonResponse({"code": 1002, "error": "missing_params"}, status=400)
        d = redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {}
        if not d or d.get("user_id") != uid:
            raise BusinessError(4001, "goal_not_found", 404)
        update = {}
        for k in ("goal_name", "description", "target_date", "status"):
            if k in body and body.get(k) is not None:
                update[k] = body.get(k)
        if update:
            redis_client.redis.hset(f"plan:goal:id:{gid}", mapping=update)
        return ok(redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {})

    if request.method == "DELETE":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            raise BusinessError(1002, "invalid_json", 400)
        uid = auth_user_id(request)
        gid = body.get("goal_id")
        d = redis_client.redis.hgetall(f"plan:goal:id:{gid}") or {}
        if not d or d.get("user_id") != uid:
            raise BusinessError(4001, "goal_not_found", 404)
        cur = redis_client.redis.get(_list_key(uid)) or ""
        ids = [x for x in cur.split(",") if x and x != gid]
        redis_client.redis.set(_list_key(uid), ",".join(ids))
        return ok({"deleted": True})

    raise BusinessError(405, "method_not_allowed", 405)
