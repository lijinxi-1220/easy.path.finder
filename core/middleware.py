import time
import uuid
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from core.utils import err
from core.exceptions import BusinessError
from core.logger import log
from users.api.auth import auth_user_id


class RequestIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rid = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        request.request_id = rid
        return None

    def process_response(self, request, response):
        rid = getattr(request, "request_id", str(uuid.uuid4()))
        response["X-Request-ID"] = rid
        return response


class AccessLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_ts = time.time()
        return None

    def process_response(self, request, response):
        try:
            duration_ms = int((time.time() - getattr(request, "_start_ts", time.time())) * 1000)
            rid = getattr(request, "request_id", "")
            uid = auth_user_id(request)
            log("info", request_id=rid, method=request.method, path=request.path, status=response.status_code, duration_ms=duration_ms, user_id=uid)
        except Exception:
            pass
        return response


class ExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        rid = getattr(request, "request_id", str(uuid.uuid4()))
        try:
            log("error", request_id=rid, path=request.path, error=str(exception))
        except Exception:
            pass
        if isinstance(exception, BusinessError):
            return err(exception.code, exception.message, status=exception.status)
        return err(500, "internal_error", status=500)
