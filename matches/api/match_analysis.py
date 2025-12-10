import json
import uuid
from datetime import datetime, UTC

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.utils import ok, err
from resumes.repo import ResumeRepo
from users.api.auth import auth_user_id, token_role
from ..repo import MatchesRepo


@csrf_exempt
@require_POST
def match_analysis(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return err(ErrorCode.REQUEST_ERROR)
    user_token_uid = auth_user_id(request)
    provided_uid = body.get("user_id")
    resume_id = body.get("resume_id")
    target_type = (body.get("target_type") or "").lower()
    target_id = body.get("target_id")
    if provided_uid and provided_uid != user_token_uid:
        bearer = request.headers.get("Authorization", "")
        token = bearer.split(" ", 1)[1] if bearer.startswith("Bearer ") else ""
        if token_role(token) != "admin":
            return err(ErrorCode.PERMISSION_DENIED)
        user_id = provided_uid
    else:
        user_id = user_token_uid
    if not user_id or not resume_id or not target_type:
        return err(ErrorCode.USER_INFO_INCOMPLETE)
    r = ResumeRepo.get(resume_id)
    if not r or r.get("user_id") != user_id:
        return err(ErrorCode.USER_INFO_INCOMPLETE)
    if target_type == "job":
        exists = bool(MatchesRepo.get_job_profile(target_id)) if target_id else True
        if not exists:
            return err(ErrorCode.JOB_PROFILE_NOT_FOUND)
    elif target_type == "school":
        exists = bool(MatchesRepo.get_school(target_id)) if target_id else True
        if not exists:
            return err(ErrorCode.TARGET_NOT_FOUND)
    else:
        return err(ErrorCode.MISSING_PARAMS)

    # 简易匹配：根据简历长度与目标类型给出百分比
    parsed_size = 1000
    try:
        parsed = json.loads(r.get("parsed_content") or "{}")
        parsed_size = int(parsed.get("size", 1000))
    except json.JSONDecodeError:
        parsed_size = 1000
    base = 60 if target_type == "job" else 65
    percentage = max(50, min(97, base + parsed_size // 5000))
    details = {
        "skills": percentage - 3,
        "experience": percentage - 5,
        "education": percentage - 6,
    }
    match_id = str(uuid.uuid4())
    MatchesRepo.create_match(
        match_id,
        mapping={
            "match_id": match_id,
            "user_id": user_id,
            "resume_id": resume_id,
            "target_type": target_type,
            "target_id": target_id or "",
            "match_percentage": str(percentage),
            "match_details": json.dumps(details),
            "generated_date": datetime.now(UTC).isoformat(),
        },
    )
    return ok({
        "match_id": match_id,
        "match_percentage": percentage,
        "match_details": details,
    })
