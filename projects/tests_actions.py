from django.test import TestCase
from django.urls import reverse

from projects.models import Project, Skill
from users.models import User


class ProjectActionResponseTests(TestCase):
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
        self.project = Project.objects.create(
            owner=self.owner,
            name="Demo project",
            description="Описание",
        )
        self.project.participants.add(self.owner)
        self.skill = Skill.objects.create(name="Django")

    def test_toggle_favorite_response_has_unified_shape(self):
        self.client.force_login(self.member)

        response = self.client.post(reverse("projects:toggle_favorite", kwargs={"pk": self.project.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "favorited": True, "favorite": True},
        )

    def test_toggle_participation_returns_error_payload_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse("projects:toggle_participation", kwargs={"pk": self.project.pk}))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("Автор", response.json()["message"])

    def test_complete_project_returns_message_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse("projects:complete", kwargs={"pk": self.project.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["project_status"], Project.STATUS_CLOSED)
        self.assertIn("заверш", response.json()["message"].lower())

    def test_add_project_skill_returns_unified_payload(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data={"name": "Docker"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["added"])
        self.assertEqual(payload["name"], "Docker")

    def test_remove_project_skill_returns_ok_status(self):
        self.project.skills.add(self.skill)
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:remove_skill", kwargs={"pk": self.project.pk, "skill_id": self.skill.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
