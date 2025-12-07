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
    "sort_by_allowed": {"name", "years", "fee"},
    "sort_by_default": "name",
    "sort_order_default": "asc",
})
def mentors(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    field = (request.GET.get("field") or "").lower()
    v = getattr(request, "validated", {})
    page = v["page"]
    page_size = v["page_size"]
    sort_by = v["sort_by"]
    sort_order = v["sort_order"]
    ids = ServicesRepo.get_mentor_ids(field)
    if not ids:
        raise BusinessError(6002, "no_mentors", 404)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    items = []
    for mid in ids[start:end]:
        d = ServicesRepo.get_mentor(mid) or {}
        items.append({
            "name": d.get("name", ""),
            "title": d.get("title", ""),
            "years": d.get("years", ""),
            "fee": d.get("fee", ""),
            "id": mid,
        })
    def keyfunc(x):
        if sort_by in ("years", "fee"):
            try:
                return int(x.get(sort_by) or 0)
            except Exception:
                return 0
        return x.get(sort_by) or ""
    items.sort(key=keyfunc, reverse=(sort_order == "desc"))
    return ok({"mentors": items, "meta": {"total": len(ids), "page": page, "page_size": page_size}})
