from django.test import Client, TestCase

from projects.models import Project, Skill
from users.forms import ProjectForm, UserProfileForm
from users.models import User


class TeamFinderSmokeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123",
            name="Owner",
            surname="User",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="StrongPass123",
            name="Member",
            surname="User",
        )
        self.skill = Skill.objects.create(name="Django")
        self.project = Project.objects.create(
            owner=self.owner,
            name="Demo project",
            description="Описание",
        )
        self.project.participants.add(self.owner)
        self.client = Client()

    def test_public_pages_render(self):
        self.assertEqual(self.client.get("/projects/list/").status_code, 200)
        self.assertEqual(self.client.get("/users/list/").status_code, 200)
        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/").status_code, 200)

    def test_email_login_works(self):
        response = self.client.post(
            "/users/login/",
            {"email": "owner@example.com", "password": "StrongPass123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_toggle_favorite_requires_login_and_works(self):
        response = self.client.post(f"/projects/{self.project.pk}/toggle-favorite/")
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.member)
        response = self.client.post(f"/projects/{self.project.pk}/toggle-favorite/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorited"])
        self.assertTrue(self.member.favorites.filter(pk=self.project.pk).exists())

    def test_owner_can_add_skill_to_project(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            f"/projects/{self.project.pk}/skills/add/",
            data='{"skill_id": %d}' % self.skill.pk,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["skill_id"], self.skill.pk)
        self.assertTrue(payload["added"])
        self.assertTrue(self.project.skills.filter(pk=self.skill.pk).exists())

    def test_complete_project_returns_status_payload(self):
        self.client.force_login(self.owner)
        response = self.client.post(f"/projects/{self.project.pk}/complete/")
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(response.json()["project_status"], Project.STATUS_CLOSED)
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)

    def test_profile_form_normalizes_phone_and_validates_github(self):
        form = UserProfileForm(
            data={
                "name": self.owner.name,
                "surname": self.owner.surname,
                "about": "about",
                "phone": "8 (999) 123-45-67",
                "github_url": "https://github.com/example",
            },
            instance=self.owner,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["phone"], "+79991234567")

        bad_form = UserProfileForm(
            data={
                "name": self.owner.name,
                "surname": self.owner.surname,
                "about": "about",
                "phone": "+79991234567",
                "github_url": "https://gitlab.com/example",
            },
            instance=self.owner,
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
