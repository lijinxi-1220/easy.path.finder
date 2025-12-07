import uuid
from django.http import JsonResponse


def ok(data, status=200):
    return JsonResponse(data, status=status)


def err(code, message, status=400):
    return JsonResponse({"code": code, "error": message}, status=status)


def parse_int(value, default):
    try:
        return int(value)
    except Exception:
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

