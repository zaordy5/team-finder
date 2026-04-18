from django.test import TestCase

from projects.models import Project, Skill
from projects.services import ProjectActionError
from projects.services import complete_project_for_owner
from projects.services import remove_skill_from_project
from projects.services import toggle_project_favorite
from projects.services import toggle_project_participation
from users.models import User


class ProjectActionServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner-service@example.com',
            password='StrongPass123',
            name='Owner',
            surname='Service',
        )
        self.member = User.objects.create_user(
            email='member-service@example.com',
            password='StrongPass123',
            name='Member',
            surname='Service',
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name='Service project',
            description='Описание',
        )
        self.project.participants.add(self.owner)
        self.skill = Skill.objects.create(name='Python')

    def test_toggle_project_favorite_returns_message_and_updates_state(self):
        payload = toggle_project_favorite(self.member, self.project)
        self.assertTrue(payload['favorited'])
        self.assertIn('избранное', payload['message'].lower())
        self.assertTrue(self.member.favorites.filter(pk=self.project.pk).exists())

        payload = toggle_project_favorite(self.member, self.project)
        self.assertFalse(payload['favorited'])
        self.assertFalse(self.member.favorites.filter(pk=self.project.pk).exists())

    def test_owner_cannot_toggle_participation_for_own_project(self):
        with self.assertRaises(ProjectActionError) as exc:
            toggle_project_participation(self.owner, self.project)
        self.assertEqual(exc.exception.status_code, 400)

    def test_closed_project_rejects_participation(self):
        self.project.status = Project.STATUS_CLOSED
        self.project.save(update_fields=['status'])

        with self.assertRaises(ProjectActionError) as exc:
            toggle_project_participation(self.member, self.project)
        self.assertEqual(exc.exception.status_code, 400)

    def test_only_owner_can_complete_project(self):
        with self.assertRaises(ProjectActionError) as exc:
            complete_project_for_owner(self.member, self.project)
        self.assertEqual(exc.exception.status_code, 403)

        payload = complete_project_for_owner(self.owner, self.project)
        self.project.refresh_from_db()
        self.assertEqual(payload['project_status'], Project.STATUS_CLOSED)
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)

    def test_remove_skill_requires_existing_relation(self):
        with self.assertRaises(ProjectActionError) as exc:
            remove_skill_from_project(self.owner, self.project, self.skill)
        self.assertEqual(exc.exception.status_code, 400)

        self.project.skills.add(self.skill)
        payload = remove_skill_from_project(self.owner, self.project, self.skill)
        self.assertEqual(payload['status'], 'ok')
        self.assertFalse(self.project.skills.filter(pk=self.skill.pk).exists())
