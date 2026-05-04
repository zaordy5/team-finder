from django.db.models import QuerySet

from .models import User


FILTER_OWNERS_OF_FAVORITES = "owners-of-favorite-projects"
FILTER_OWNERS_OF_PARTICIPATING = "owners-of-participating-projects"
FILTER_INTERESTED_IN_MY_PROJECTS = "interested-in-my-projects"
FILTER_PARTICIPANTS_OF_MY_PROJECTS = "participants-of-my-projects"

VARIANT_ONE_FILTERS = {
    FILTER_OWNERS_OF_FAVORITES,
    FILTER_OWNERS_OF_PARTICIPATING,
    FILTER_INTERESTED_IN_MY_PROJECTS,
    FILTER_PARTICIPANTS_OF_MY_PROJECTS,
}


def apply_variant_one_filter(
    queryset: QuerySet[User],
    current_user: User,
    filter_name: str,
) -> QuerySet[User]:
    if filter_name not in VARIANT_ONE_FILTERS:
        return queryset

    if filter_name == FILTER_OWNERS_OF_FAVORITES:
        owner_ids = current_user.favorites.values_list("owner_id", flat=True)
        return queryset.filter(id__in=owner_ids)

    if filter_name == FILTER_OWNERS_OF_PARTICIPATING:
        owner_ids = current_user.participating_projects.values_list("owner_id", flat=True)
        return queryset.filter(id__in=owner_ids)

    if filter_name == FILTER_INTERESTED_IN_MY_PROJECTS:
        interested_user_ids = (
            User.objects.filter(favorites__owner=current_user)
            .exclude(id=current_user.id)
            .values_list("id", flat=True)
        )
        return queryset.filter(id__in=interested_user_ids)

    # Последний разрешённый фильтр — участники проектов текущего пользователя.
    participant_ids = (
        User.objects.filter(participating_projects__owner=current_user)
        .exclude(id=current_user.id)
        .values_list("id", flat=True)
    )
    return queryset.filter(id__in=participant_ids)