from django.conf import settings
from django.db import models


SKILL_NAME_MAX_LENGTH = 124
PROJECT_NAME_MAX_LENGTH = 200
PROJECT_STATUS_MAX_LENGTH = 6


class Skill(models.Model):
    name = models.CharField(
        "Название навыка",
        max_length=SKILL_NAME_MAX_LENGTH,
        unique=True,
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "навык"
        verbose_name_plural = "навыки"

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    class Status(models.TextChoices):
        # TextChoices помогает хранить статусы в одном месте и не дублировать строки.
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    name = models.CharField("Название", max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField("Описание", blank=True)
    github_url = models.URLField("Ссылка на GitHub", blank=True)
    status = models.CharField(
        "Статус",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Участники",
        related_name="participating_projects",
        blank=True,
    )
    favorited_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Добавили в избранное",
        related_name="favorites",
        blank=True,
    )
    skills = models.ManyToManyField(
        Skill,
        verbose_name="Необходимые навыки",
        related_name="projects",
        blank=True,
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        # Так в списках первыми будут показываться недавно созданные проекты.
        ordering = ["-created_at"]
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return f"/projects/{self.pk}/"