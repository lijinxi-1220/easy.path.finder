import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import UploadedFile
from .. import redis_client
from .. import config as rconfig
from users.api.auth import auth_user_id, token_role, resolve_user_id
from core.utils import ok, err


def _file_ext(name: str):
    name = (name or "").lower()
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".docx"):
        return "docx"
    return None


@csrf_exempt
def upload_parse(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    if not redis_client.redis:
        return err(500, "redis_not_configured", status=500)

    provided_uid = request.POST.get("user_id") or (request.GET.get("user_id") or "")
    user_id = resolve_user_id(request, provided_uid)
    if not user_id:
        from core.exceptions import ErrorCode
        return err(ErrorCode.PERMISSION_DENIED)
    resume_name = request.POST.get("resume_name") or ""
    upfile: UploadedFile | None = request.FILES.get("resume_file")

    if not upfile:
        # 允许后续通过 JSON 传 base64 文件，简化：此处直接判失败
        return err(2002, "parse_failed")

    ext = _file_ext(upfile.name)
    if not ext:
        return err(2001, "format_not_supported", status=415)
    if upfile.size > rconfig.MAX_FILE_MB * 1024 * 1024:
        return err(2003, "file_too_large", status=413)

    resume_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    file_url = f"urn:resume:{resume_id}:{upfile.name}"

    # 伪解析：仅存储文件基本信息；后续可接入真实解析服务
    skills_raw = request.POST.get("skills")
    skills = []
    if skills_raw:
        try:
            val = json.loads(skills_raw)
            if isinstance(val, list):
                skills = [str(s) for s in val]
        except Exception:
            skills = [s.strip() for s in str(skills_raw).split(",") if s.strip()]

    parsed_content = json.dumps({
        "name": resume_name or upfile.name,
        "size": upfile.size,
        "format": ext,
        "skills": skills,
    })
    parse_status = "parsed"

    redis_client.redis.hset(
        f"resume:id:{resume_id}",
        mapping={
            "resume_id": resume_id,
            "user_id": user_id,
            "resume_name": resume_name or upfile.name,
            "file_url": file_url,
            "parsed_content": parsed_content,
            "parse_status": parse_status,
            "created_at": created_at,
            "is_default": "0",
        },
    )
    # 列表维护
    key_list = f"resume:list:{user_id}"
    cur = redis_client.redis.get(key_list) or ""
    items = [x for x in cur.split(",") if x]
    items.append(resume_id)
    redis_client.redis.set(key_list, ",".join(items))

    return ok({
        "resume_id": resume_id,
        "file_url": file_url,
        "parsed_content": json.loads(parsed_content),
        "parse_status": parse_status,
    })
