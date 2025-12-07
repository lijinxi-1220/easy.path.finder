from django.views.decorators.http import require_GET
from .. import redis_client
from ..repo import MatchesRepo
from core.utils import ok
from core.exceptions import BusinessError


@require_GET
def school_detail(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    sid = request.GET.get("school_id") or ""
    if not sid:
        raise BusinessError(1002, "missing_params", 400)
    data = MatchesRepo.get_school(sid) or {}
    if not data:
        raise BusinessError(3004, "school_not_found", 404)
    return ok(data)
