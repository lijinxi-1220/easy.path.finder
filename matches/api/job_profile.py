from django.views.decorators.http import require_GET
from .. import redis_client
from ..repo import MatchesRepo
from core.utils import ok
from core.exceptions import BusinessError


@require_GET
def job_profile(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    job_title = (request.GET.get("job_title") or "").strip().lower()
    industry = (request.GET.get("industry") or "").strip().lower()
    if not job_title:
        raise BusinessError(1002, "missing_params", 400)
    pid = MatchesRepo.get_job_profile_id(job_title, industry)
    if not pid:
        raise BusinessError(3001, "job_profile_not_found", 404)
    data = MatchesRepo.get_job_profile(pid) or {}
    if not data:
        raise BusinessError(3001, "job_profile_not_found", 404)
    return ok(data)


@require_GET
def job_detail(request):
    if not redis_client.redis:
        raise BusinessError(500, "redis_not_configured", 500)
    pid = request.GET.get("job_profile_id") or ""
    if not pid:
        raise BusinessError(1002, "missing_params", 400)
    data = MatchesRepo.get_job_profile(pid) or {}
    if not data:
        raise BusinessError(3001, "job_profile_not_found", 404)
    return ok(data)
