from django.test import Client, TestCase
from django.urls import reverse

from projects.models import Project, Skill
from users.models import User


class UserViewTests(TestCase):
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

    def test_email_login_works(self):
        response = self.client.post(
            reverse("users:login"),
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
