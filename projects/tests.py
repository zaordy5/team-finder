from django.test import Client, TestCase
from django.urls import reverse

from projects.models import Project, Skill
from projects.services import ProjectActionError
from projects.services import complete_project_for_owner
from projects.services import remove_skill_from_project
from projects.services import toggle_project_favorite
from projects.services import toggle_project_participation
from users.forms import ProjectForm
from users.models import User


class BaseProjectTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email="owner-service@example.com",
            password="StrongPass123",
            name="Owner",
            surname="Service",
        )
        self.member = User.objects.create_user(
            email="member-service@example.com",
            password="StrongPass123",
            name="Member",
            surname="Service",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="Service project",
            description="Описание",
        )
        self.project.participants.add(self.owner)
        self.skill = Skill.objects.create(name="Python")


class ProjectActionServiceTests(BaseProjectTestCase):
    def test_toggle_project_favorite_updates_state(self):
        payload = toggle_project_favorite(self.user, self.project)

        self.user.refresh_from_db()
        self.assertTrue(self.user.favorites.filter(pk=self.project.pk).exists())
        self.assertEqual(
            payload,
            {
                "status": "ok",
                "favorited": True,
                "favorite": True,
            },
        )

        payload = toggle_project_favorite(self.user, self.project)

        self.user.refresh_from_db()
        self.assertFalse(self.user.favorites.filter(pk=self.project.pk).exists())
        self.assertEqual(
            payload,
            {
                "status": "ok",
                "favorited": False,
                "favorite": False,
            },
        )

    def test_owner_cannot_toggle_participation_for_own_project(self):
        with self.assertRaises(ProjectActionError) as exc:
            toggle_project_participation(self.owner, self.project)
        self.assertEqual(exc.exception.status_code, 400)

    def test_closed_project_rejects_participation(self):
        self.project.status = Project.STATUS_CLOSED
        self.project.save(update_fields=["status"])

        with self.assertRaises(ProjectActionError) as exc:
            toggle_project_participation(self.member, self.project)
        self.assertEqual(exc.exception.status_code, 400)

    def test_only_owner_can_complete_project(self):
        with self.assertRaises(ProjectActionError) as exc:
            complete_project_for_owner(self.member, self.project)
        self.assertEqual(exc.exception.status_code, 403)

        payload = complete_project_for_owner(self.owner, self.project)
        self.project.refresh_from_db()
        self.assertEqual(payload["project_status"], Project.STATUS_CLOSED)
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)

    def test_remove_skill_requires_existing_relation(self):
        with self.assertRaises(ProjectActionError) as exc:
            remove_skill_from_project(self.owner, self.project, self.skill)
        self.assertEqual(exc.exception.status_code, 400)

        self.project.skills.add(self.skill)
        payload = remove_skill_from_project(self.owner, self.project, self.skill)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(self.project.skills.filter(pk=self.skill.pk).exists())


class ProjectViewPermissionsTests(BaseProjectTestCase):
    def test_guest_is_redirected_from_create_project_page(self):
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_owner_can_create_project_and_becomes_participant(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "New project",
                "description": "Новый проект",
                "github_url": "https://github.com/example/new-project",
                "status": Project.STATUS_OPEN,
            },
        )

        self.assertEqual(response.status_code, 302)
        created_project = Project.objects.get(name="New project")
        self.assertEqual(created_project.owner, self.owner)
        self.assertTrue(created_project.participants.filter(pk=self.owner.pk).exists())

    def test_non_owner_cannot_open_project_edit_page(self):
        self.client.force_login(self.member)

        response = self.client.get(reverse("projects:edit", kwargs={"pk": self.project.pk}))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_edit_project(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:edit", kwargs={"pk": self.project.pk}),
            {
                "name": "Updated service project",
                "description": "Обновлённое описание",
                "github_url": "https://github.com/example/service-project",
                "status": Project.STATUS_OPEN,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated service project")
        self.assertEqual(self.project.description, "Обновлённое описание")

    def test_non_owner_cannot_complete_project(self):
        self.client.force_login(self.member)

        response = self.client.post(reverse("projects:complete", kwargs={"pk": self.project.pk}))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "error")

    def test_owner_can_complete_project_via_view(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse("projects:complete", kwargs={"pk": self.project.pk}))

        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)
        self.assertEqual(response.json()["project_status"], Project.STATUS_CLOSED)

    def test_authenticated_user_can_join_and_leave_foreign_project(self):
        self.client.force_login(self.member)

        join_response = self.client.post(reverse("projects:toggle_participation", kwargs={"pk": self.project.pk}))
        self.assertEqual(join_response.status_code, 200)
        self.assertTrue(join_response.json()["participant"])
        self.assertTrue(self.project.participants.filter(pk=self.member.pk).exists())

        leave_response = self.client.post(reverse("projects:toggle_participation", kwargs={"pk": self.project.pk}))
        self.assertEqual(leave_response.status_code, 200)
        self.assertFalse(leave_response.json()["participant"])
        self.assertFalse(self.project.participants.filter(pk=self.member.pk).exists())

    def test_guest_is_redirected_from_participation_action(self):
        response = self.client.post(reverse("projects:toggle_participation", kwargs={"pk": self.project.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)


class ProjectFormTests(BaseProjectTestCase):
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

    def test_project_form_trims_name_and_description(self):
        form = ProjectForm(
            data={
                "name": "   Demo name   ",
                "description": "   demo description   ",
                "github_url": "https://github.com/example/repo",
                "status": Project.STATUS_OPEN,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["name"], "Demo name")
        self.assertEqual(form.cleaned_data["description"], "demo description")
