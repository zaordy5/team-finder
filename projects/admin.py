from django.contrib import admin

from .models import Project, Skill


ADMIN_LIST_PER_PAGE = 25


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = ADMIN_LIST_PER_PAGE


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "status",
        "participant_count",
        "favorite_count",
        "created_at",
    )
    list_filter = ("status", "created_at", "skills")
    search_fields = (
        "name",
        "description",
        "owner__email",
        "owner__name",
        "owner__surname",
    )
    autocomplete_fields = (
        "owner",
        "participants",
        "favorited_by",
        "skills",
    )
    list_select_related = ("owner",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = ADMIN_LIST_PER_PAGE
    ordering = ("-created_at",)

    @admin.display(description="Участники")
    def participant_count(self, obj: Project) -> int:
        # Счётчики удобнее смотреть сразу в списке проектов.
        return obj.participants.count()

    @admin.display(description="В избранном")
    def favorite_count(self, obj: Project) -> int:
        return obj.favorited_by.count()