import json
import uuid
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from users.api.auth import auth_user_id
from core.utils import ok
from core.validators import validate_query
from core.exceptions import BusinessError


def _goal_key(gid):
    return f"plan:goal:id:{gid}"


def _task_list_key(gid):
    return f"plan:task:list:{gid}"


def _task_key(tid):
    return f"plan:task:id:{tid}"


@csrf_exempt
def tasks_generate(request):
    if request.method != "POST":
        raise BusinessError(405, "method_not_allowed", 405)
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        raise BusinessError(1002, "invalid_json", 400)
    uid = auth_user_id(request)
    gid = body.get("goal_id")
    d = redis_client.redis.hgetall(_goal_key(gid)) or {}
    if not d or d.get("user_id") != uid:
        raise BusinessError(4001, "goal_not_found", 404)
    base = datetime.utcnow()
    tasks = [
        {"task_name": "完善技能清单", "due_date": (base + timedelta(days=7)).isoformat(), "priority": "high"},
        {"task_name": "投递简历", "due_date": (base + timedelta(days=14)).isoformat(), "priority": "medium"},
        {"task_name": "面试准备", "due_date": (base + timedelta(days=21)).isoformat(), "priority": "medium"},
    ]
    created = []
    for t in tasks:
        tid = str(uuid.uuid4())
        redis_client.redis.hset(_task_key(tid), mapping={
            "task_id": tid,
            "goal_id": gid,
            "user_id": uid,
            "task_name": t["task_name"],
            "due_date": t["due_date"],
            "priority": t["priority"],
            "status": "pending",
            "created_at": base.isoformat(),
        })
        created.append(tid)
    cur = redis_client.redis.get(_task_list_key(gid)) or ""
    ids = [x for x in cur.split(",") if x] + created
    redis_client.redis.set(_task_list_key(gid), ",".join(ids))
    items = [redis_client.redis.hgetall(_task_key(tid)) for tid in created]
    return ok({"tasks": items})


@csrf_exempt
def tasks_manage(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    uid = auth_user_id(request)
    if request.method == "GET":
        gid = request.GET.get("goal_id") or ""
        d = redis_client.redis.hgetall(_goal_key(gid)) or {}
        if not d or d.get("user_id") != uid:
            raise BusinessError(4001, "goal_not_found", 404)
        cur = redis_client.redis.get(_task_list_key(gid)) or ""
        ids = [x for x in cur.split(",") if x]
        items = [redis_client.redis.hgetall(_task_key(tid)) for tid in ids]
        # filters
        status = (request.GET.get("status") or "").strip()
        priority = (request.GET.get("priority") or "").strip()
        due_from = request.GET.get("due_from") or ""
        due_to = request.GET.get("due_to") or ""
        if status:
            items = [it for it in items if (it.get("status") or "") == status]
        if priority:
            items = [it for it in items if (it.get("priority") or "") == priority]
        if due_from:
            items = [it for it in items if (it.get("due_date") or "") >= due_from]
        if due_to:
            items = [it for it in items if (it.get("due_date") or "") <= due_to]
        # sort + pagination via validator
        from core.validators import validate_query as _v
        @(_v({
            "params": {
                "sort_by": {"type": "str", "default": "due_date", "enum": {"due_date", "priority", "created_at", "task_name", "status"}},
                "sort_order": {"type": "str", "default": "asc", "enum": {"asc", "desc"}},
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
        page = v["page"]
        page_size = v["page_size"]
        total = len(items)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return ok({"tasks": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}})

    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            raise BusinessError(1002, "invalid_json", 400)
        gid = body.get("goal_id")
        name = body.get("task_name")
        if not gid or not name:
            return JsonResponse({"code": 1002, "error": "missing_params"}, status=400)
        d = redis_client.redis.hgetall(_goal_key(gid)) or {}
        if not d or d.get("user_id") != uid:
            raise BusinessError(4001, "goal_not_found", 404)
        tid = str(uuid.uuid4())
        redis_client.redis.hset(_task_key(tid), mapping={
            "task_id": tid,
            "goal_id": gid,
            "user_id": uid,
            "task_name": name,
            "due_date": body.get("due_date", ""),
            "priority": body.get("priority", "low"),
            "status": body.get("status", "pending"),
            "created_at": datetime.utcnow().isoformat(),
        })
        cur = redis_client.redis.get(_task_list_key(gid)) or ""
        ids = [x for x in cur.split(",") if x] + [tid]
        redis_client.redis.set(_task_list_key(gid), ",".join(ids))
        return ok(redis_client.redis.hgetall(_task_key(tid)))

    if request.method == "PUT":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            raise BusinessError(1002, "invalid_json", 400)
        tid = body.get("task_id")
        t = redis_client.redis.hgetall(_task_key(tid)) or {}
        if not t or t.get("user_id") != uid:
            raise BusinessError(4003, "task_not_found", 404)
        update = {}
        for k in ("task_name", "due_date", "priority", "status"):
            if k in body and body.get(k) is not None:
                update[k] = body.get(k)
        if update:
            redis_client.redis.hset(_task_key(tid), mapping=update)
        return ok(redis_client.redis.hgetall(_task_key(tid)))

    raise BusinessError(405, "method_not_allowed", 405)
