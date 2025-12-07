from django.http import JsonResponse
from core.utils import ok
from core.validators import validate_query
from core.exceptions import BusinessError
from django.views.decorators.http import require_GET
from services import redis_client
from services.repo import ServicesRepo


@require_GET
@validate_query({
    "page_default": 1,
    "page_size_default": 20,
    "sort_by_allowed": {"name", "time", "location", "method"},
    "sort_by_default": "name",
    "sort_order_default": "asc",
})
def projects(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    pt = (request.GET.get("project_type") or "").lower()
    v = getattr(request, "validated", {})
    page = v["page"]
    page_size = v["page_size"]
    sort_by = v["sort_by"]
    sort_order = v["sort_order"]
    ids = ServicesRepo.get_project_ids(pt)
    items = []
    for pid in ids:
        d = ServicesRepo.get_project(pid) or {}
        if d:
            items.append({
                "name": d.get("name", ""),
                "intro": d.get("intro", ""),
                "time": d.get("time", ""),
                "location": d.get("location", ""),
                "method": d.get("method", ""),
            })
    if not items:
        raise BusinessError(6005, "no_projects", 404)
    items.sort(key=lambda x: x.get(sort_by) or "", reverse=(sort_order == "desc"))
    total = len(items)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return ok({"projects": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}})
