from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import AdminUserChangeForm, AdminUserCreationForm
from .models import User


ADMIN_LIST_PER_PAGE = 25


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm

    list_display = (
        "email",
        "name",
        "surname",
        "phone",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    search_fields = (
        "email",
        "name",
        "surname",
        "phone",
        "github_url",
    )
    ordering = ("-date_joined",)
    list_per_page = ADMIN_LIST_PER_PAGE

    readonly_fields = ("last_login", "date_joined")
    filter_horizontal = ("groups", "user_permissions", "skills")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "name",
                    "surname",
                    "about",
                    "phone",
                    "github_url",
                    "avatar",
                    "skills",
                ),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                # При создании пользователя в админке оставлены только основные поля.
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )