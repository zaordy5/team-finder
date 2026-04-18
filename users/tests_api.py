from django.test import TestCase
from django.urls import reverse

from projects.models import Skill
from users.models import User


class UserSkillResponseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPass123",
            name="Demo",
            surname="User",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123",
            name="Other",
            surname="User",
        )
        self.skill = Skill.objects.create(name="Django")

    def test_add_user_skill_returns_unified_payload(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("users:add_skill"),
            data={"skill_id": self.skill.pk},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["skill_id"], self.skill.pk)
        self.assertTrue(payload["added"])

    def test_remove_user_skill_returns_forbidden_payload_for_foreign_profile(self):
        self.other_user.skills.add(self.skill)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("users:remove_skill_for_user", kwargs={"pk": self.other_user.pk, "skill_id": self.skill.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("прав", response.json()["message"].lower())
