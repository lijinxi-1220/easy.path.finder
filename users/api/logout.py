from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .auth import blacklist_token
from core.utils import ok, err


@csrf_exempt
def logout(request):
    if request.method != "POST":
        return err(405, "method_not_allowed", status=405)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return err(1007, "invalid_token", status=401)
    token = auth.split(" ", 1)[1]
    ok_flag, err_msg = blacklist_token(token)
    if not ok_flag:
        return err(1011 if err_msg == "token_expired" else 1010, err_msg, status=401)
    return ok({"success": True})
