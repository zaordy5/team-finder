from __future__ import annotations

from django.db.models import QuerySet

from users.models import User


VARIANT_ONE_FILTERS = {
    "owners-of-favorite-projects",
    "owners-of-participating-projects",
    "interested-in-my-projects",
    "participants-of-my-projects",
}


def apply_variant_one_filter(queryset: QuerySet[User], current_user: User, filter_name: str) -> QuerySet[User]:
    if filter_name not in VARIANT_ONE_FILTERS:
        return queryset

    if filter_name == "owners-of-favorite-projects":
        owner_ids = current_user.favorites.values_list("owner_id", flat=True)
        return queryset.filter(id__in=owner_ids)

    if filter_name == "owners-of-participating-projects":
        owner_ids = current_user.participating_projects.values_list("owner_id", flat=True)
        return queryset.filter(id__in=owner_ids)

    if filter_name == "interested-in-my-projects":
        interested_user_ids = (
            User.objects.filter(favorites__owner=current_user)
            .exclude(id=current_user.id)
            .values_list("id", flat=True)
        )
        return queryset.filter(id__in=interested_user_ids)

    participant_ids = (
        User.objects.filter(participating_projects__owner=current_user)
        .exclude(id=current_user.id)
        .values_list("id", flat=True)
    )
    return queryset.filter(id__in=participant_ids)
