from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from users.forms import ProjectForm
from .models import Project, Skill
from .services import ProjectActionError
from .services import add_skill_to_project
from .services import complete_project_for_owner
from .services import remove_skill_from_project
from .services import toggle_project_favorite
from .services import toggle_project_participation



def _query_without_page(request: HttpRequest) -> str:
    params = request.GET.copy()
    params.pop('page', None)
    encoded = params.urlencode()
    return f'&{encoded}' if encoded else ''


@require_GET
def skill_lookup(request: HttpRequest) -> JsonResponse:
    query = request.GET.get('q', '').strip()
    skills = Skill.objects.all()
    if query:
        skills = skills.filter(name__istartswith=query)
    return JsonResponse(list(skills.order_by('name').values('id', 'name')[:10]), safe=False)


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        queryset = Project.objects.select_related('owner').prefetch_related('participants', 'skills')
        active_skill = self.request.GET.get('skill', '').strip()
        if active_skill:
            queryset = queryset.filter(skills__name__iexact=active_skill)
        return queryset.distinct().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_skill'] = self.request.GET.get('skill', '').strip()
        context['all_skills'] = Skill.objects.filter(projects__isnull=False).distinct().order_by('name')
        context['query_without_page'] = _query_without_page(self.request)
        return context


class FavoriteProjectsView(LoginRequiredMixin, ListView):
    template_name = 'projects/favorite_projects.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        return self.request.user.favorites.select_related('owner').prefetch_related('participants', 'skills').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query_without_page'] = _query_without_page(self.request)
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project-details.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.select_related('owner').prefetch_related('participants', 'skills', 'favorited_by')


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        self.object.participants.add(self.request.user)
        return response

    def get_success_url(self):
        return f'/projects/{self.object.pk}/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if project.owner != request.user:
            return HttpResponseForbidden('Вы не можете редактировать этот проект.')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return f'/projects/{self.object.pk}/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


@login_required
@require_POST
def toggle_favorite(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    payload = toggle_project_favorite(request.user, project)
    return JsonResponse(payload)


@login_required
@require_POST
def toggle_participation(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project.objects.prefetch_related('participants'), pk=pk)
    try:
        payload = toggle_project_participation(request.user, project)
    except ProjectActionError as exc:
        return JsonResponse({'status': 'error', 'message': exc.message}, status=exc.status_code)
    return JsonResponse(payload)


@login_required
@require_POST
def complete_project(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    try:
        payload = complete_project_for_owner(request.user, project)
    except ProjectActionError as exc:
        return JsonResponse({'status': 'error', 'message': exc.message}, status=exc.status_code)
    return JsonResponse(payload)


@login_required
@require_POST
def add_project_skill(request: HttpRequest, pk: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    try:
        payload = add_skill_to_project(request.user, project, request)
    except ProjectActionError as exc:
        return JsonResponse({'status': 'error', 'message': exc.message}, status=exc.status_code)
    return JsonResponse(payload)


@login_required
@require_POST
def remove_project_skill(request: HttpRequest, pk: int, skill_id: int) -> JsonResponse:
    project = get_object_or_404(Project, pk=pk)
    skill = get_object_or_404(Skill, pk=skill_id)
    try:
        payload = remove_skill_from_project(request.user, project, skill)
    except ProjectActionError as exc:
        return JsonResponse({'status': 'error', 'message': exc.message}, status=exc.status_code)
    return JsonResponse(payload)
