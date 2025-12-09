from django.views.decorators.http import require_GET

from core.exceptions import BusinessError
from core.utils import ok, err
from core.validators import validate_query
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
    field = (request.GET.get("field") or "").lower()
    v = getattr(request, "validated", {})
    page = v["page"]
    page_size = v["page_size"]
    sort_by = v["sort_by"]
    sort_order = v["sort_order"]
    ids = ServicesRepo.get_mentor_ids(field)
    if not ids:
        return err(BusinessError(6002, "no_mentors", 404))
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
    def _func(x):
        if sort_by in ("years", "fee"):
            try:
                return int(x.get(sort_by) or 0)
            except ValueError:
                return 0
        return x.get(sort_by) or ""
    items.sort(key=_func, reverse=(sort_order == "desc"))
    return ok({"mentors": items, "meta": {"total": len(ids), "page": page, "page_size": page_size}})
