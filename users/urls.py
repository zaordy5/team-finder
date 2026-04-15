from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("edit-profile/", views.ProfileUpdateView.as_view(), name="edit_profile"),
    path("list/", views.UserListView.as_view(), name="list"),
    path("skills/", views.skill_lookup, name="skill_lookup"),
    path("skills/add/", views.add_user_skill, name="add_skill"),
    path("skills/<int:skill_id>/remove/", views.remove_user_skill, name="remove_skill"),
    path("<int:pk>/skills/add/", views.add_user_skill, name="add_skill_for_user"),
    path("<int:pk>/skills/<int:skill_id>/remove/", views.remove_user_skill, name="remove_skill_for_user"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="detail"),
]
