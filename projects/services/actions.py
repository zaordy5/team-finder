from dataclasses import dataclass

from django.http import HttpRequest

from team_finder.helpers import resolve_skill_from_request
from projects.models import Project, Skill
from users.models import User


@dataclass(slots=True)
class ProjectActionError(Exception):
    message: str
    status_code: int = 400


def toggle_project_favorite(user: User, project: Project) -> dict:
    is_favorited = user.favorites.filter(pk=project.pk).exists()
    if is_favorited:
        user.favorites.remove(project)
        return {
            'status': 'ok',
            'favorited': False,
            'favorite': False,
            'message': 'Проект удалён из избранного.',
        }

    user.favorites.add(project)
    return {
        'status': 'ok',
        'favorited': True,
        'favorite': True,
        'message': 'Проект добавлен в избранное.',
    }


def toggle_project_participation(user: User, project: Project) -> dict:
    if project.owner_id == user.pk:
        raise ProjectActionError('Автор проекта уже является участником.', status_code=400)
    if project.status == Project.STATUS_CLOSED:
        raise ProjectActionError('Нельзя присоединиться к закрытому проекту.', status_code=400)

    is_participant = project.participants.filter(pk=user.pk).exists()
    if is_participant:
        project.participants.remove(user)
        return {
            'status': 'ok',
            'participant': False,
            'message': 'Вы вышли из числа участников проекта.',
        }

    project.participants.add(user)
    return {
        'status': 'ok',
        'participant': True,
        'message': 'Вы присоединились к проекту.',
    }


def complete_project_for_owner(user: User, project: Project) -> dict:
    if project.owner_id != user.pk:
        raise ProjectActionError('Недостаточно прав для завершения проекта.', status_code=403)

    if project.status != Project.STATUS_OPEN:
        return {
            'status': 'ok',
            'project_status': project.status,
            'message': 'Проект уже закрыт.',
        }

    project.status = Project.STATUS_CLOSED
    project.save(update_fields=['status', 'updated_at'])
    return {
        'status': 'ok',
        'project_status': Project.STATUS_CLOSED,
        'message': 'Проект успешно завершён.',
    }


def add_skill_to_project(user: User, project: Project, request: HttpRequest) -> dict:
    if project.owner_id != user.pk:
        raise ProjectActionError('Недостаточно прав для изменения навыков проекта.', status_code=403)

    try:
        skill, created = resolve_skill_from_request(request)
    except ValueError as exc:
        raise ProjectActionError(str(exc), status_code=400) from exc

    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)

    return {
        'status': 'ok',
        'skill_id': skill.id,
        'created': created,
        'added': added,
        'id': skill.id,
        'name': skill.name,
        'message': 'Навык добавлен.' if added else 'Такой навык уже есть у проекта.',
    }


def remove_skill_from_project(user: User, project: Project, skill: Skill) -> dict:
    if project.owner_id != user.pk:
        raise ProjectActionError('Недостаточно прав для изменения навыков проекта.', status_code=403)

    if not project.skills.filter(pk=skill.pk).exists():
        raise ProjectActionError('У проекта нет такого навыка.', status_code=400)

    project.skills.remove(skill)
    return {
        'status': 'ok',
        'skill_id': skill.pk,
        'message': 'Навык удалён.',
    }
