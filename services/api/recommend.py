from django.http import JsonResponse
from core.utils import ok
from core.validators import validate_query
from core.exceptions import BusinessError
from django.views.decorators.http import require_GET
from users.api.auth import auth_user_id
from services import redis_client
from services.repo import ServicesRepo


@require_GET
@validate_query({
    "page_default": 1,
    "page_size_default": 20,
    "sort_by_allowed": {"name", "provider"},
    "sort_by_default": "name",
    "sort_order_default": "asc",
})
def recommend(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    uid = auth_user_id(request)
    st = (request.GET.get("service_type") or "").lower()
    v = getattr(request, "validated", {})
    page = v["page"]
    page_size = v["page_size"]
    sort_by = v["sort_by"]
    sort_order = v["sort_order"]
    if not uid or st not in {"course", "internship"}:
        raise BusinessError(6001, "no_match", 404)
    ids = ServicesRepo.get_svc_ids(st)
    items = []
    for sid in [x for x in ids if x]:
        d = ServicesRepo.get_svc(st, sid) or {}
        if d:
            items.append({
                "name": d.get("name", ""),
                "intro": d.get("intro", ""),
                "provider": d.get("provider", ""),
                "link": d.get("link", ""),
            })
    if not items:
        raise BusinessError(6001, "no_match", 404)
    items.sort(key=lambda x: x.get(sort_by) or "", reverse=(sort_order == "desc"))
    total = len(items)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return ok({"recommendations": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}})
