from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, FormView, ListView, UpdateView

from projects.models import Skill
from projects.utils import resolve_skill_from_request
from team_finder.constants import DEFAULT_PAGE_SIZE, SKILL_LOOKUP_LIMIT
from team_finder.query import query_without_page

from .filters import apply_variant_one_filter
from .forms import EmailAuthenticationForm, UserProfileForm, UserRegistrationForm
from .models import User


class RegisterView(FormView):
    template_name = "users/register.html"
    form_class = UserRegistrationForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Аккаунт создан. Теперь войдите в систему.")
        return redirect("users:login")


class LoginView(FormView):
    template_name = "users/login.html"
    form_class = EmailAuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect("projects:list")


@login_required
@require_POST
def add_user_skill(request: HttpRequest, pk: int | None = None) -> JsonResponse:
    profile_user = request.user if pk is None else get_object_or_404(User, pk=pk)
    if profile_user != request.user:
        return JsonResponse(
            {"status": "error", "message": "Недостаточно прав."},
            status=HTTPStatus.FORBIDDEN,
        )
    try:
        skill, created = resolve_skill_from_request(request)
    except ValueError as exc:
        return JsonResponse(
            {"status": "error", "message": str(exc)},
            status=HTTPStatus.BAD_REQUEST,
        )
    added = not profile_user.skills.filter(pk=skill.pk).exists()
    if added:
        profile_user.skills.add(skill)
    return JsonResponse(
        {
            "status": "ok",
            "skill_id": skill.id,
            "created": created,
            "added": added,
            "id": skill.id,
            "name": skill.name,
            "message": "Навык добавлен." if added else "Такой навык уже есть в профиле.",
        }
    )


@login_required
@require_POST
def remove_user_skill(request: HttpRequest, skill_id: int, pk: int | None = None) -> JsonResponse:
    profile_user = request.user if pk is None else get_object_or_404(User, pk=pk)
    if profile_user != request.user:
        return JsonResponse(
            {"status": "error", "message": "Недостаточно прав."},
            status=HTTPStatus.FORBIDDEN,
        )
    skill = get_object_or_404(Skill, pk=skill_id)
    if not profile_user.skills.filter(pk=skill.pk).exists():
        return JsonResponse(
            {"status": "error", "message": "У пользователя нет такого навыка."},
            status=HTTPStatus.BAD_REQUEST,
        )
    profile_user.skills.remove(skill)
    return JsonResponse(
        {"status": "ok", "message": "Навык удалён.", "skill_id": skill.pk}
    )


@require_GET
def skill_lookup(request: HttpRequest) -> JsonResponse:
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.all()
    if query:
        skills = skills.filter(name__istartswith=query)
    payload = list(
        skills.order_by("name").values("id", "name")[:SKILL_LOOKUP_LIMIT]
    )
    return JsonResponse(payload, safe=False)


@login_required
def logout_view(request: HttpRequest):
    logout(request)
    return redirect("projects:list")


class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = "users/change_password.html"
    form_class = PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Пароль обновлён.")
        return redirect("users:detail", pk=self.request.user.pk)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "users/edit_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return self.request.user.get_absolute_url()


class UserDetailView(DetailView):
    model = User
    template_name = "users/user-details.html"
    context_object_name = "user"


class UserListView(ListView):
    model = User
    template_name = "users/participants.html"
    context_object_name = "participants"
    paginate_by = DEFAULT_PAGE_SIZE

    def get_queryset(self):
        queryset = User.objects.all().prefetch_related("skills")
        filter_name = self.request.GET.get("filter", "")
        active_skill = self.request.GET.get("skill", "").strip()

        if self.request.user.is_authenticated and filter_name:
            queryset = apply_variant_one_filter(queryset, self.request.user, filter_name)
        if active_skill:
            queryset = queryset.filter(skills__name__iexact=active_skill)
        return queryset.distinct().order_by("-date_joined")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_filter"] = self.request.GET.get("filter", "")
        context["active_skill"] = self.request.GET.get("skill", "").strip()
        context["all_skills"] = Skill.objects.filter(users__isnull=False).distinct().order_by("name")
        context["query_without_page"] = query_without_page(self.request)
        return context
