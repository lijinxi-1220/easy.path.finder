import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .. import redis_client
from .. import config as rconfig
from users.api.auth import resolve_user_id
from core.utils import ok, err


@csrf_exempt
def export(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)
    provided_uid = request.POST.get("user_id") or ""
    resume_id = request.POST.get("resume_id") or ""
    template_id = request.POST.get("template_id") or ""
    export_format = (request.POST.get("export_format") or "").lower()
    user_id = resolve_user_id(request, provided_uid)
    if not user_id:
        return err(1006, "permission_denied", status=403)
    r = redis_client.redis.hgetall(f"resume:id:{resume_id}")
    if not r or r.get("user_id") != user_id:
        return err(2004, "resume_not_found", status=404)
    if template_id not in rconfig.ALLOWED_EXPORT_TEMPLATES:
        return err(2006, "template_not_found", status=404)
    if export_format not in {"pdf", "docx"}:
        return err(2007, "export_failed")
    file_name = f"{r.get('resume_name') or 'resume'}_{template_id}.{export_format}"
    export_url = f"https://example.com/download/{uuid.uuid4()}/{file_name}"
    return ok({"export_url": export_url, "file_name": file_name})
