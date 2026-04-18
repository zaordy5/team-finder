from __future__ import annotations

from django.http import JsonResponse


def ok_response(*, status: int = 200, message: str | None = None, **payload) -> JsonResponse:
    data = {"status": "ok", **payload}
    if message:
        data["message"] = message
    return JsonResponse(data, status=status)


def error_response(message: str, *, status: int = 400, **payload) -> JsonResponse:
    data = {"status": "error", "message": message, **payload}
    return JsonResponse(data, status=status)
