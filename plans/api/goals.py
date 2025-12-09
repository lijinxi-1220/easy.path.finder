import json
import uuid
from datetime import datetime, UTC

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.utils import ok, err
from plans.repo import PlansRepo
from users.api.auth import auth_user_id


def _list_key(user_id):
    return f"plan:goal:list:{user_id}"


@csrf_exempt
@require_POST
def goals(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    uid = auth_user_id(request)
    action = (body.get("action") or "").lower()
    if action == "list":
        items_raw = PlansRepo.list_goals_by_user(uid)
        items = []
        for d in items_raw:
            if d:
                items.append({
                    "goal_id": d.get("goal_id"),
                    "goal_name": d.get("goal_name"),
                    "status": d.get("status", "active"),
                    "target_date": d.get("target_date", ""),
                    "created_at": d.get("created_at", ""),
                })
        status = (str(body.get("status") or "").strip())
        q = (str(body.get("q") or "").strip().lower())
        due_from = body.get("due_from") or ""
        due_to = body.get("due_to") or ""
        if status:
            items = [it for it in items if (it.get("status") or "") == status]
        if q:
            items = [it for it in items if q in (it.get("goal_name") or "").lower()]
        if due_from:
            items = [it for it in items if (it.get("target_date") or "") >= due_from]
        if due_to:
            items = [it for it in items if (it.get("target_date") or "") <= due_to]
        sort_by = (body.get("sort_by") or "created_at")
        sort_order = (body.get("sort_order") or "desc")
        items.sort(key=lambda x: x.get(sort_by) or "", reverse=(sort_order == "desc"))
        page = int(body.get("page") or 1)
        page_size = int(body.get("page_size") or 20)
        total = len(items)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return ok({"goals": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}})
    if action == "get":
        gid = body.get("goal_id") or ""
        data = PlansRepo.get_goal(gid) or {}
        if not data or data.get("user_id") != uid:
            return err(ErrorCode.GOAL_NOT_FOUND)
        return ok(data)
    if action == "update":
        gid = body.get("goal_id")
        if not gid:
            return err(ErrorCode.MISSING_PARAMS)
        d = PlansRepo.get_goal(gid) or {}
        if not d or d.get("user_id") != uid:
            return err(ErrorCode.GOAL_NOT_FOUND)
        update = {}
        for k in ("goal_name", "description", "target_date", "status"):
            if k in body and body.get(k) is not None:
                update[k] = body.get(k)
        if update:
            PlansRepo.update_goal(gid, mapping=update)
        return ok(PlansRepo.get_goal(gid) or {})
    if action == "delete":
        gid = body.get("goal_id")
        d = PlansRepo.get_goal(gid) or {}
        if not d or d.get("user_id") != uid:
            return err(ErrorCode.GOAL_NOT_FOUND)
        PlansRepo.remove_goal_from_user(uid, gid)
        return ok({"deleted": True})
    # default create
    goal_name = body.get("goal_name")
    desc = body.get("description") or ""
    target_date = body.get("target_date") or ""
    if not uid or not goal_name:
        return err(ErrorCode.MISSING_PARAMS)
    gid = str(uuid.uuid4())
    PlansRepo.create_goal(gid, mapping={
        "goal_id": gid,
        "user_id": uid,
        "goal_name": goal_name,
        "description": desc,
        "target_date": target_date,
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
    })
    PlansRepo.add_goal_to_user(uid, gid)
    return ok(PlansRepo.get_goal(gid) or {})
