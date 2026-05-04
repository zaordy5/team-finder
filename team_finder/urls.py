from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def redirect_to_projects(request):
    return redirect("projects:list")


urlpatterns = [
    path("", redirect_to_projects, name="home"),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls", namespace="users")),
    path("projects/", include("projects.urls", namespace="projects")),
]

if settings.DEBUG:
    # В режиме разработки отдаём загруженные пользователями файлы через Django.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)