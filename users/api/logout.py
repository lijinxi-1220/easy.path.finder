from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.exceptions import ErrorCode
from core.utils import ok, err
from .auth import blacklist_token


@csrf_exempt
@require_POST
def logout(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return err(ErrorCode.CREDENTIALS_ERROR)
    token = auth.split(" ", 1)[1]
    ok_flag, err_msg = blacklist_token(token)
    if not ok_flag:
        return err(ErrorCode.CREDENTIALS_ERROR)
    return ok({"success": True})
