from django.test import Client, TestCase
from django.urls import reverse

from projects.models import Project, Skill
from users.models import User


class ProjectViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123",
            name="Owner",
            surname="User",
        )
        self.other_owner = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123",
            name="Other",
            surname="Owner",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="StrongPass123",
            name="Member",
            surname="User",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="Demo project",
            description="Описание",
        )
        self.project.participants.add(self.owner)
        self.second_project = Project.objects.create(
            owner=self.other_owner,
            name="Second project",
            description="Второй проект",
        )
        self.second_project.participants.add(self.other_owner)
        self.skill = Skill.objects.create(name="Django")
        self.client = Client()

    def test_public_pages_render(self):
        self.assertEqual(self.client.get(reverse("projects:list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("users:list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("projects:detail", kwargs={"pk": self.project.pk})).status_code, 200)

    def test_toggle_favorite_requires_login_and_works(self):
        response = self.client.post(reverse("projects:toggle_favorite", kwargs={"pk": self.project.pk}))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.member)
        response = self.client.post(reverse("projects:toggle_favorite", kwargs={"pk": self.project.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorited"])
        self.assertTrue(self.member.favorites.filter(pk=self.project.pk).exists())

    def test_favorite_projects_page_shows_only_user_favorites(self):
        self.member.favorites.add(self.project)
        self.client.force_login(self.member)

        response = self.client.get(reverse("projects:favorites"))

        self.assertEqual(response.status_code, 200)
        page_projects = list(response.context["projects"])
        self.assertIn(self.project, page_projects)
        self.assertNotIn(self.second_project, page_projects)

    def test_owner_can_add_skill_to_project(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
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
        response = self.client.post(reverse("projects:complete", kwargs={"pk": self.project.pk}))
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(response.json()["project_status"], Project.STATUS_CLOSED)
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)
