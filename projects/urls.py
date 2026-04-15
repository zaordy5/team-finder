from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.ProjectListView.as_view(), name="list"),
    path("favorites/", views.FavoriteProjectsView.as_view(), name="favorites"),
    path("create-project/", views.ProjectCreateView.as_view(), name="create"),
    path("skills/", views.skill_lookup, name="skill_lookup"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
    path("<int:pk>/complete/", views.complete_project, name="complete"),
    path("<int:pk>/toggle-participate/", views.toggle_participation, name="toggle_participation"),
    path("<int:pk>/toggle-favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("<int:pk>/skills/add/", views.add_project_skill, name="add_skill"),
    path("<int:pk>/skills/<int:skill_id>/remove/", views.remove_project_skill, name="remove_skill"),
]
