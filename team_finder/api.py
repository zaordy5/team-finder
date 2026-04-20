from http import HTTPStatus

from django.http import JsonResponse


def ok_response(*, status: HTTPStatus = HTTPStatus.OK, message: str | None = None, **payload) -> JsonResponse:
    data = {"status": "ok", **payload}
    if message:
        data["message"] = message
    return JsonResponse(data, status=status)


def error_response(
    message: str,
    *,
    status: HTTPStatus = HTTPStatus.BAD_REQUEST,
    **payload,
) -> JsonResponse:
    data = {"status": "error", "message": message, **payload}
    return JsonResponse(data, status=status)
