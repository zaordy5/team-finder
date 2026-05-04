import json
from typing import Any

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from .models import Skill


def get_request_payload(request: HttpRequest) -> dict[str, Any]:
    if not request.body:
        return {}

    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def resolve_skill_from_request(request: HttpRequest) -> tuple[Skill, bool]:
    payload = get_request_payload(request)
    skill_id = payload.get("skill_id")
    skill_name = (payload.get("name") or "").strip()

    if skill_id:
        return get_object_or_404(Skill, pk=skill_id), False

    if not skill_name:
        raise ValueError("Skill name or id is required")

    # Если навыка ещё нет, создаём его сразу из формы/JSON-запроса.
    skill, created = Skill.objects.get_or_create(name=skill_name)
    return skill, created