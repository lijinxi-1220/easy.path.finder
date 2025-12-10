import uuid
from django.http import JsonResponse

from core.config import is_debug
from core.exceptions import BusinessError


def ok(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def err(error: BusinessError):
    print(error.__traceback__)
    if is_debug():
        return JsonResponse({"code": error.code, "error": error.message, "stack": error.__traceback__},
                            status=error.status, json_dumps_params={'ensure_ascii': False})
    return JsonResponse({"code": error.code, "error": error.message}, status=error.status)


def parse_int(value, default):
    try:
        return int(value)
    except ValueError:
        return default


def get_pagination_params(request, default_page=1, default_size=20):
    page = parse_int(request.GET.get("page"), default_page)
    size = parse_int(request.GET.get("page_size"), default_size)
    return max(1, page), max(1, size)


def apply_pagination(items, page, page_size):
    total = len(items)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return items[start:end], {"total": total, "page": page, "page_size": page_size}


def new_request_id():
    return str(uuid.uuid4())
