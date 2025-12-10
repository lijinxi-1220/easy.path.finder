import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..repo import ResumeRepo
from ..repo import ResumeRepo
from users.api.auth import resolve_user_id, auth_user_id
from core.utils import ok, err
from core.exceptions import ErrorCode


@csrf_exempt
@require_POST
def manage(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    action = (body.get("action") or "").lower()
    provided_uid = body.get("user_id") or ""
    user_id = resolve_user_id(request, provided_uid)
    if not user_id:
        return err(ErrorCode.PERMISSION_DENIED)

    if action == "list":
        items = []
        for r in ResumeRepo.list_by_user(user_id):
            if r:
                items.append({
                    "resume_id": r.get("resume_id"),
                    "resume_name": r.get("resume_name"),
                    "is_default": r.get("is_default") == "1",
                })
        return ok({"resumes": items})

    if action == "update":
        resume_id = body.get("resume_id")
        if not resume_id:
            return err(ErrorCode.REQUEST_ERROR)
        r = ResumeRepo.get(resume_id)
        if not r or r.get("user_id") != user_id:
            return err(ErrorCode.RESUME_NOT_FOUND)
        update = {}
        if body.get("resume_name") is not None:
            update["resume_name"] = body.get("resume_name")
        if body.get("is_default") is not None:
            is_default = body.get("is_default")
            update["is_default"] = "1" if is_default else "0"
            if is_default:
                for rid_item in [x.get("resume_id") for x in ResumeRepo.list_by_user(user_id) if x.get("resume_id")]:
                    ResumeRepo.update(rid_item, {"is_default": "0"})
        if update:
            ResumeRepo.update(resume_id, update)
        return ok({"resume": ResumeRepo.get(resume_id)})

    if action == "delete":
        resume_id = body.get("resume_id")
        if not resume_id:
            return err(ErrorCode.REQUEST_ERROR)
        r = ResumeRepo.get(resume_id)
        if not r or r.get("user_id") != user_id:
            return err(ErrorCode.RESUME_NOT_FOUND)
        if r.get("is_default") == "1":
            return err(ErrorCode.DEFAULT_NOT_DELETABLE)
        cur_items = ResumeRepo.list_by_user(user_id)
        ids = [x.get("resume_id") for x in cur_items if x.get("resume_id") and x.get("resume_id") != resume_id]
        ResumeRepo.set_user_list(user_id, ids)
        return ok({"deleted": True})

    # default: get single by id
    if action == "get":
        resume_id = body.get("resume_id")
        r = ResumeRepo.get(resume_id)
        if not r or r.get("user_id") != user_id:
            return err(ErrorCode.RESUME_NOT_FOUND)
        return ok({"resume": r})

    return err(ErrorCode.REQUEST_ERROR)
