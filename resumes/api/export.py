import uuid

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.utils import ok, err
from resumes.repo import ResumeRepo
from users.api.auth import resolve_user_id
from core import redis_client
from core.exceptions import ErrorCode


@csrf_exempt
@require_POST
def export(request):
    provided_uid = request.POST.get("user_id") or ""
    resume_id = request.POST.get("resume_id") or ""
    template_id = request.POST.get("template_id") or ""
    export_format = (request.POST.get("export_format") or "").lower()
    user_id = resolve_user_id(request, provided_uid)
    if not user_id:
        return err(ErrorCode.PERMISSION_DENIED)
    r = ResumeRepo.get(resume_id)
    if not r or r.get("user_id") != user_id:
        return err(ErrorCode.RESUME_NOT_FOUND)
    file_name = f"{r.get('resume_name') or 'resume'}_{template_id}.{export_format}"
    export_url = f"https://example.com/download/{uuid.uuid4()}/{file_name}"
    return ok({"export_url": export_url, "file_name": file_name})
