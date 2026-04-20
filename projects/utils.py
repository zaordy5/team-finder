import json

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from .models import Skill


def get_request_payload(request: HttpRequest) -> dict:
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def resolve_skill_from_request(request: HttpRequest):
    payload = get_request_payload(request)
    skill_id = payload.get("skill_id")
    name = (payload.get("name") or "").strip()
    if skill_id:
        return get_object_or_404(Skill, pk=skill_id), False
    if not name:
        raise ValueError("Skill name or id is required")
    skill, created = Skill.objects.get_or_create(name=name)
    return skill, created
