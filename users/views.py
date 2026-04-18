from django.conf import settings
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
from team_finder.helpers import resolve_skill_from_request
from .forms import EmailAuthenticationForm, UserProfileForm, UserRegistrationForm
from .models import User


TASK_VERSION = str(getattr(settings, "TASK_VERSION", "1"))


def _query_without_page(request: HttpRequest) -> str:
    params = request.GET.copy()
    params.pop("page", None)
    encoded = params.urlencode()
    return f"&{encoded}" if encoded else ""


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
        return JsonResponse({"status": "error", "message": "Недостаточно прав."}, status=403)
    try:
        skill, created = resolve_skill_from_request(request)
    except ValueError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    added = not profile_user.skills.filter(pk=skill.pk).exists()
    if added:
        profile_user.skills.add(skill)
    return JsonResponse({
        "skill_id": skill.id,
        "created": created,
        "added": added,
        "id": skill.id,
        "name": skill.name,
    })


@login_required
@require_POST
def remove_user_skill(request: HttpRequest, skill_id: int, pk: int | None = None) -> JsonResponse:
    profile_user = request.user if pk is None else get_object_or_404(User, pk=pk)
    if profile_user != request.user:
        return JsonResponse({"status": "error", "message": "Недостаточно прав."}, status=403)
    skill = get_object_or_404(Skill, pk=skill_id)
    profile_user.skills.remove(skill)
    return JsonResponse({"status": "ok"})


@require_GET
def skill_lookup(request: HttpRequest) -> JsonResponse:
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.all()
    if query:
        skills = skills.filter(name__istartswith=query)
    payload = list(skills.order_by("name").values("id", "name")[:10])
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
    paginate_by = 12

    def get_queryset(self):
        queryset = User.objects.all().prefetch_related("skills")
        filter_name = self.request.GET.get("filter", "")
        active_skill = self.request.GET.get("skill", "").strip()

        if self.request.user.is_authenticated and filter_name:
            queryset = self._apply_variant_one_filter(queryset, filter_name)
        if active_skill:
            queryset = queryset.filter(skills__name__iexact=active_skill)
        return queryset.distinct().order_by("-date_joined")

    def _apply_variant_one_filter(self, queryset, filter_name: str):
        user = self.request.user
        if filter_name == "owners-of-favorite-projects":
            owner_ids = user.favorites.values_list("owner_id", flat=True)
            return queryset.filter(id__in=owner_ids)
        if filter_name == "owners-of-participating-projects":
            owner_ids = user.participated_projects.values_list("owner_id", flat=True)
            return queryset.filter(id__in=owner_ids)
        if filter_name == "interested-in-my-projects":
            user_ids = User.objects.filter(favorites__owner=user).values_list("id", flat=True)
            return queryset.filter(id__in=user_ids).exclude(id=user.id)
        if filter_name == "participants-of-my-projects":
            user_ids = User.objects.filter(participating_projects__owner=user).values_list("id", flat=True)
            return queryset.filter(id__in=user_ids).exclude(id=user.id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_filter"] = self.request.GET.get("filter", "")
        context["active_skill"] = self.request.GET.get("skill", "").strip()
        context["all_skills"] = Skill.objects.filter(users__isnull=False).distinct().order_by("name")
        context["query_without_page"] = _query_without_page(self.request)
        context["task_version"] = TASK_VERSION
        return context
