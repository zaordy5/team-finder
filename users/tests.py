from django.test import Client, TestCase
from django.urls import reverse

from projects.models import Project, Skill
from users.forms import ProjectForm, UserProfileForm, UserRegistrationForm
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
        self.other_owner = User.objects.create_user(
            email="other-owner@example.com",
            password="StrongPass123",
            name="Other",
            surname="Owner",
        )
        self.fan = User.objects.create_user(
            email="fan@example.com",
            password="StrongPass123",
            name="Fan",
            surname="User",
        )
        self.skill = Skill.objects.create(name="Django")
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

    def test_registration_redirects_to_login_and_creates_user(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Anna",
                "surname": "Ivanova",
                "email": "anna-new@example.com",
                "password": "StrongPass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("users:login"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="anna-new@example.com").exists())

    def test_toggle_favorite_requires_login_and_works(self):
        response = self.client.post(f"/projects/{self.project.pk}/toggle-favorite/")
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.member)
        response = self.client.post(f"/projects/{self.project.pk}/toggle-favorite/")
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

    def test_change_password_updates_credentials(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("users:change_password"),
            {
                "old_password": "StrongPass123",
                "new_password1": "NewStrongPass456",
                "new_password2": "NewStrongPass456",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("users:detail", kwargs={"pk": self.owner.pk}),
            fetch_redirect_response=False,
        )
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("NewStrongPass456"))

        self.client.logout()
        login_response = self.client.post(
            reverse("users:login"),
            {"email": self.owner.email, "password": "NewStrongPass456"},
            follow=True,
        )
        self.assertTrue(login_response.wsgi_request.user.is_authenticated)

    def test_user_avatar_is_generated_automatically(self):
        user = User.objects.create_user(
            email="avatar@example.com",
            password="StrongPass123",
            name="Avatar",
            surname="Tester",
        )
        self.assertTrue(bool(user.avatar))

    def test_filter_owners_of_favorite_projects(self):
        self.member.favorites.add(self.second_project)
        self.client.force_login(self.member)

        response = self.client.get(reverse("users:list"), {"filter": "owners-of-favorite-projects"})

        self.assertEqual(response.status_code, 200)
        participants = list(response.context["participants"])
        self.assertEqual(participants, [self.other_owner])

    def test_filter_owners_of_participating_projects(self):
        self.second_project.participants.add(self.member)
        self.client.force_login(self.member)

        response = self.client.get(reverse("users:list"), {"filter": "owners-of-participating-projects"})

        self.assertEqual(response.status_code, 200)
        participants = list(response.context["participants"])
        self.assertEqual(participants, [self.other_owner])

    def test_filter_interested_in_my_projects(self):
        self.fan.favorites.add(self.project)
        self.client.force_login(self.owner)

        response = self.client.get(reverse("users:list"), {"filter": "interested-in-my-projects"})

        self.assertEqual(response.status_code, 200)
        participants = list(response.context["participants"])
        self.assertEqual(participants, [self.fan])

    def test_filter_participants_of_my_projects(self):
        self.project.participants.add(self.member)
        self.client.force_login(self.owner)

        response = self.client.get(reverse("users:list"), {"filter": "participants-of-my-projects"})

        self.assertEqual(response.status_code, 200)
        participants = list(response.context["participants"])
        self.assertEqual(participants, [self.member])


    def test_registration_form_normalizes_email_and_rejects_duplicate(self):
        form = UserRegistrationForm(
            data={
                "name": "  Anna ",
                "surname": "  Ivanova ",
                "email": " NEWUSER@EXAMPLE.COM ",
                "password": "StrongPass123",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.name, "Anna")
        self.assertEqual(user.surname, "Ivanova")

        duplicate_form = UserRegistrationForm(
            data={
                "name": "New",
                "surname": "User",
                "email": "OWNER@EXAMPLE.COM",
                "password": "StrongPass123",
            }
        )
        self.assertFalse(duplicate_form.is_valid())
        self.assertIn("email", duplicate_form.errors)

    def test_profile_form_rejects_invalid_phone_and_scheme(self):
        form = UserProfileForm(
            data={
                "name": self.owner.name,
                "surname": self.owner.surname,
                "about": "about",
                "phone": "12345",
                "github_url": "ftp://github.com/example",
            },
            instance=self.owner,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
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
