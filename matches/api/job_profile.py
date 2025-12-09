from django.views.decorators.http import require_GET

from core.exceptions import ErrorCode
from core.utils import ok, err
from ..repo import MatchesRepo


@require_GET
def job_profile(request):
    job_title = (request.GET.get("job_title") or "").strip().lower()
    industry = (request.GET.get("industry") or "").strip().lower()
    if not job_title:
        return err(ErrorCode.REQUEST_ERROR)
    pid = MatchesRepo.get_job_profile_id(job_title, industry)
    if not pid:
        return err(ErrorCode.JOB_PROFILE_NOT_FOUND)
    data = MatchesRepo.get_job_profile(pid) or {}
    if not data:
        return err(ErrorCode.JOB_PROFILE_NOT_FOUND)
    return ok(data)


@require_GET
def job_detail(request):
    pid = request.GET.get("job_profile_id") or ""
    if not pid:
        return err(ErrorCode.REQUEST_ERROR)
    data = MatchesRepo.get_job_profile(pid) or {}
    if not data:
        return err(ErrorCode.JOB_PROFILE_NOT_FOUND)
    return ok(data)
