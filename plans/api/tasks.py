import json
import uuid
from datetime import datetime, timedelta, UTC

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import BusinessError, ErrorCode
from core.utils import ok, err
from plans.repo import PlansRepo
from users.api.auth import auth_user_id


def _goal_key(gid):
    return f"plan:goal:id:{gid}"


def _task_list_key(gid):
    return f"plan:task:list:{gid}"


def _task_key(tid):
    return f"plan:task:id:{tid}"

@csrf_exempt
@require_POST
def tasks_manage(request):
    uid = auth_user_id(request)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    action = (body.get("action") or "").lower()
    if action == "list":
        gid = body.get("goal_id") or ""
        d = PlansRepo.get_goal(gid) or {}
        if not d or d.get("user_id") != uid:
            return err(ErrorCode.GOAL_NOT_FOUND)
        items = PlansRepo.list_tasks_by_goal(gid)
        status = (str(body.get("status") or "").strip())
        priority = (str(body.get("priority") or "").strip())
        due_from = body.get("due_from") or ""
        due_to = body.get("due_to") or ""
        if status:
            items = [it for it in items if (it.get("status") or "") == status]
        if priority:
            items = [it for it in items if (it.get("priority") or "") == priority]
        if due_from:
            items = [it for it in items if (it.get("due_date") or "") >= due_from]
        if due_to:
            items = [it for it in items if (it.get("due_date") or "") <= due_to]
        sort_by = (body.get("sort_by") or "due_date")
        sort_order = (body.get("sort_order") or "asc")
        items.sort(key=lambda x: x.get(sort_by) or "", reverse=(sort_order == "desc"))
        page = int(body.get("page") or 1)
        page_size = int(body.get("page_size") or 20)
        total = len(items)
        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return ok({"tasks": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}})
    if action == "generate":
        gid = body.get("goal_id")
        d = PlansRepo.get_goal(gid) or {}
        if not d or d.get("user_id") != uid:
            return err(ErrorCode.GOAL_NOT_FOUND)
        base = datetime.now(UTC)
        tasks = [
            {"task_name": "完善技能清单", "due_date": (base + timedelta(days=7)).isoformat(), "priority": "high"},
            {"task_name": "投递简历", "due_date": (base + timedelta(days=14)).isoformat(), "priority": "medium"},
            {"task_name": "面试准备", "due_date": (base + timedelta(days=21)).isoformat(), "priority": "medium"},
        ]
        created = []
        for t in tasks:
            tid = str(uuid.uuid4())
            PlansRepo.create_task(tid, mapping={
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
        for tid in created:
            PlansRepo.add_task_to_goal(gid, tid)
        items = [PlansRepo.get_task(tid) for tid in created]
        return ok({"tasks": items})
    gid = body.get("goal_id")
    name = body.get("task_name")
    if not gid or not name:
        return err(ErrorCode.REQUEST_ERROR)
    d = PlansRepo.get_goal(gid) or {}
    if not d or d.get("user_id") != uid:
        return err(ErrorCode.GOAL_NOT_FOUND)
    tid = str(uuid.uuid4())
    PlansRepo.create_task(tid, mapping={
        "task_id": tid,
        "goal_id": gid,
        "user_id": uid,
        "task_name": name,
        "due_date": body.get("due_date", ""),
        "priority": body.get("priority", "low"),
        "status": body.get("status", "pending"),
        "created_at": datetime.now(UTC).isoformat(),
    })
    PlansRepo.add_task_to_goal(gid, tid)
    return ok(PlansRepo.get_task(tid))
