import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from ..repo import ResumeRepo
from users.api.auth import resolve_user_id, auth_user_id
from core.utils import ok, err


@csrf_exempt
def manage(request):
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    if request.method == "GET":
        user_id = resolve_user_id(request, request.GET.get("user_id") or "")
        if not user_id:
            return err(1006, "permission_denied", status=403)
        items = []
        for r in ResumeRepo.list_by_user(user_id):
            if r:
                items.append({
                    "resume_id": r.get("resume_id"),
                    "resume_name": r.get("resume_name"),
                    "is_default": r.get("is_default") == "1",
                })
        return ok({"resumes": items})

    if request.method == "PUT":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            return err(1002, "invalid_json")
        provided_uid = body.get("user_id")
        resume_id = body.get("resume_id")
        resume_name = body.get("resume_name")
        is_default = body.get("is_default")
        user_id = resolve_user_id(request, provided_uid)
        if not user_id:
            return err(1006, "permission_denied", status=403)
        rkey = ResumeRepo.id_key(resume_id)
        r = ResumeRepo.get(resume_id)
        if not r or r.get("user_id") != user_id:
            return err(2004, "resume_not_found", status=404)
        update = {}
        if resume_name is not None:
            update["resume_name"] = resume_name
        if is_default is not None:
            update["is_default"] = "1" if is_default else "0"
            if is_default:
                # 取消其他默认
                for rid_item in [x.get("resume_id") for x in ResumeRepo.list_by_user(user_id) if x.get("resume_id")]:
                    redis_client.redis.hset(ResumeRepo.id_key(rid_item), mapping={"is_default": "0"})
        if update:
            ResumeRepo.update(resume_id, update)
        r = ResumeRepo.get(resume_id)
        return ok({"resume": r})

    if request.method == "DELETE":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            return err(1002, "invalid_json")
        provided_uid = body.get("user_id")
        resume_id = body.get("resume_id")
        user_id = resolve_user_id(request, provided_uid)
        if not user_id:
            return err(1006, "permission_denied", status=403)
        r = ResumeRepo.get(resume_id)
        if not r or r.get("user_id") != user_id:
            return err(2004, "resume_not_found", status=404)
        if r.get("is_default") == "1":
            return err(2005, "default_not_deletable")
        cur_items = ResumeRepo.list_by_user(user_id)
        ids = [x.get("resume_id") for x in cur_items if x.get("resume_id") and x.get("resume_id") != resume_id]
        redis_client.redis.set(ResumeRepo.user_index_key(user_id), ",".join(ids))
        # 简化：保留对象，但也可删除 hash
        return ok({"deleted": True})

    return err(405, "method_not_allowed", status=405)
