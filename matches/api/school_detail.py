from django.views.decorators.http import require_GET

from core.exceptions import ErrorCode
from core.utils import ok, err
from ..repo import MatchesRepo


@require_GET
def school_detail(request):
    sid = request.GET.get("school_id") or ""
    if not sid:
        return err(ErrorCode.REQUEST_ERROR)
    data = MatchesRepo.get_school(sid) or {}
    if not data:
        return err(ErrorCode.SCHOOL_NOT_FOUND)
    return ok(data)
