from django.test import TestCase

from projects.models import Project
from users.forms import ProjectForm, UserProfileForm
from users.models import User


class UserFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123",
            name="Owner",
            surname="User",
        )

    def test_profile_form_normalizes_phone_and_validates_github(self):
        form = UserProfileForm(
            data={
                "name": self.user.name,
                "surname": self.user.surname,
                "about": "about",
                "phone": "8 (999) 123-45-67",
                "github_url": "https://github.com/example",
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["phone"], "+79991234567")

        bad_form = UserProfileForm(
            data={
                "name": self.user.name,
                "surname": self.user.surname,
                "about": "about",
                "phone": "+79991234567",
                "github_url": "https://gitlab.com/example",
            },
            instance=self.user,
        )
        self.assertFalse(bad_form.is_valid())
        self.assertIn("github_url", bad_form.errors)

    def test_project_form_validates_github_domain(self):
        form = ProjectForm(
            data={
                "name": "Proj",
                "description": "Desc",
                "github_url": "https://gitlab.com/example",
                "status": Project.STATUS_OPEN,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("github_url", form.errors)

    def test_user_avatar_is_generated_automatically(self):
        user = User.objects.create_user(
            email="avatar@example.com",
            password="StrongPass123",
            name="Avatar",
            surname="Tester",
        )
        self.assertTrue(bool(user.avatar))
