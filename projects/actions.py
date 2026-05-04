from http import HTTPStatus

from django.http import HttpRequest

from users.models import User

from .models import Project, Skill
from .utils import resolve_skill_from_request


ActionPayload = dict[str, object]


class ProjectActionError(Exception):
    def __init__(
        self,
        message: str,
        status_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _check_project_owner(user: User, project: Project, message: str) -> None:
    if project.owner_id != user.pk:
        raise ProjectActionError(message, status_code=HTTPStatus.FORBIDDEN)


def toggle_project_favorite(user: User, project: Project) -> ActionPayload:
    is_favorited = user.favorites.filter(pk=project.pk).exists()

    if is_favorited:
        user.favorites.remove(project)
        return {
            "status": "ok",
            "favorited": False,
            "favorite": False,
        }

    user.favorites.add(project)
    return {
        "status": "ok",
        "favorited": True,
        "favorite": True,
    }


def toggle_project_participation(user: User, project: Project) -> ActionPayload:
    if project.owner_id == user.pk:
        raise ProjectActionError("Автор проекта уже является участником.")

    if project.status == Project.Status.CLOSED:
        raise ProjectActionError("Нельзя присоединиться к закрытому проекту.")

    is_participant = project.participants.filter(pk=user.pk).exists()

    if is_participant:
        project.participants.remove(user)
        return {
            "status": "ok",
            "participant": False,
            "message": "Вы вышли из числа участников проекта.",
        }

    project.participants.add(user)
    return {
        "status": "ok",
        "participant": True,
        "message": "Вы присоединились к проекту.",
    }


def complete_project_for_owner(user: User, project: Project) -> ActionPayload:
    _check_project_owner(
        user,
        project,
        "Недостаточно прав для завершения проекта.",
    )

    if project.status != Project.Status.OPEN:
        return {
            "status": "ok",
            "project_status": project.status,
            "message": "Проект уже закрыт.",
        }

    # Закрываем проект только один раз, чтобы не делать лишних сохранений.
    project.status = Project.Status.CLOSED
    project.save(update_fields=["status", "updated_at"])

    return {
        "status": "ok",
        "project_status": Project.Status.CLOSED,
        "message": "Проект успешно завершён.",
    }


def add_skill_to_project(
    user: User,
    project: Project,
    request: HttpRequest,
) -> ActionPayload:
    _check_project_owner(
        user,
        project,
        "Недостаточно прав для изменения навыков проекта.",
    )

    try:
        skill, created = resolve_skill_from_request(request)
    except ValueError as exc:
        raise ProjectActionError(str(exc)) from exc

    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)

    # В ответе оставлены id и skill_id: старый JS может использовать оба поля.
    return {
        "status": "ok",
        "skill_id": skill.id,
        "created": created,
        "added": added,
        "id": skill.id,
        "name": skill.name,
        "message": "Навык добавлен." if added else "Такой навык уже есть у проекта.",
    }


def remove_skill_from_project(
    user: User,
    project: Project,
    skill: Skill,
) -> ActionPayload:
    _check_project_owner(
        user,
        project,
        "Недостаточно прав для изменения навыков проекта.",
    )

    if not project.skills.filter(pk=skill.pk).exists():
        raise ProjectActionError("У проекта нет такого навыка.")

    project.skills.remove(skill)
    return {"status": "ok"}