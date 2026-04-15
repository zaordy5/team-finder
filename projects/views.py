from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from users.forms import ProjectForm
from team_finder.helpers import resolve_skill_from_request
from .models import Project, Skill


TASK_VERSION = str(getattr(settings, "TASK_VERSION", "1"))


def _query_without_page(request: HttpRequest) -> str:
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"&{encoded}" if encoded else ""


@require_GET
def skill_lookup(request: HttpRequest) -> JsonResponse:
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.all()
    if query:
        skills = skills.filter(name__istartswith=query)
    return JsonResponse(list(skills.order_by("name").values("id", "name")[:10]), safe=False)


class ProjectListView(ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        queryset = Project.objects.select_related("owner").prefetch_related("participants", "skills")
        active_skill = self.request.GET.get("skill", "").strip()
        if active_skill:
            queryset = queryset.filter(skills__name__iexact=active_skill)
        return queryset.distinct().order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_skill"] = self.request.GET.get("skill", "").strip()
        context["all_skills"] = Skill.objects.filter(projects__isnull=False).distinct().order_by("name")
        context["query_without_page"] = _query_without_page(self.request)
        context["task_version"] = TASK_VERSION
        return context


class FavoriteProjectsView(LoginRequiredMixin, ListView):
    template_name = "projects/favorite_projects.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        return self.request.user.favorites.select_related("owner").prefetch_related("participants", "skills").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query_without_page"] = _query_without_page(self.request)
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/project-details.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.select_related("owner").prefetch_related("participants", "skills", "favorited_by")


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        self.object.participants.add(self.request.user)
        return response

    def get_success_url(self):
        return f"/projects/{self.object.pk}/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if project.owner != request.user:
            return HttpResponseForbidden("Вы не можете редактировать этот проект.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return f"/projects/{self.object.pk}/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context


@login_required
@require_POST
def toggle_favorite(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    if request.user.favorites.filter(pk=project.pk).exists():
        request.user.favorites.remove(project)
        return JsonResponse({"status": "ok", "favorited": False, "favorite": False})
    request.user.favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": True, "favorite": True})


@login_required
@require_POST
def toggle_participation(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project.objects.prefetch_related("participants"), pk=pk)
    if project.owner == request.user:
        return JsonResponse({"status": "error", "message": "Автор уже участвует в проекте."}, status=400)
    if project.status == Project.STATUS_CLOSED:
        return JsonResponse({"status": "error", "message": "Проект уже закрыт."}, status=400)

    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        return JsonResponse({"status": "ok", "participant": False})

    project.participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": True})


@login_required
@require_POST
def complete_project(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user:
        return JsonResponse({"status": "error", "message": "Недостаточно прав."}, status=403)
    if project.status != Project.STATUS_OPEN:
        return JsonResponse({"status": "ok", "project_status": project.status})
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status", "updated_at"])
    return JsonResponse({"status": "ok", "project_status": Project.STATUS_CLOSED})


@login_required
@require_POST
def add_project_skill(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user:
        return JsonResponse({"status": "error", "message": "Недостаточно прав."}, status=403)
    try:
        skill, created = resolve_skill_from_request(request)
    except ValueError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)
    return JsonResponse({
        "skill_id": skill.id,
        "created": created,
        "added": added,
        "id": skill.id,
        "name": skill.name,
    })


@login_required
@require_POST
def remove_project_skill(request: HttpRequest, pk: int, skill_id: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user:
        return JsonResponse({"status": "error", "message": "Недостаточно прав."}, status=403)
    skill = get_object_or_404(Skill, pk=skill_id)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})
