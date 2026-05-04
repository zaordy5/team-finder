from django.http import HttpRequest


def query_without_page(request: HttpRequest) -> str:
    # Убираем page, чтобы пагинация не ломала остальные активные фильтры.
    params = request.GET.copy()
    params.pop("page", None)

    encoded = params.urlencode()
    return f"&{encoded}" if encoded else ""