from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project, Skill
from users.models import User


DEMO_PASSWORD = "Teamfinder123"
ADMIN_EMAIL = "admin@teamfinder.local"
ADMIN_PASSWORD = "Admin12345"

SKILL_NAMES = [
    "Django",
    "PostgreSQL",
    "Docker",
    "React",
    "Python",
    "UI/UX",
    "DevOps",
    "QA",
]


DEMO_USERS = [
    {
        "email": "anna@example.com",
        "name": "Анна",
        "surname": "Иванова",
        "about": "Backend-разработчик, люблю Django и чистую архитектуру.",
        "phone": "+79000000001",
        "github_url": "https://github.com/anna-demo",
        "skills": ["Python", "Django", "PostgreSQL"],
    },
    {
        "email": "misha@example.com",
        "name": "Михаил",
        "surname": "Смирнов",
        "about": "Frontend-разработчик, делаю удобные интерфейсы и люблю React.",
        "phone": "+79000000002",
        "github_url": "https://github.com/misha-demo",
        "skills": ["React", "UI/UX", "QA"],
    },
    {
        "email": "olga@example.com",
        "name": "Ольга",
        "surname": "Петрова",
        "about": "DevOps-инженер, умею поднимать инфраструктуру и CI/CD.",
        "phone": "+79000000003",
        "github_url": "https://github.com/olga-demo",
        "skills": ["Docker", "DevOps", "PostgreSQL"],
    },
]


class Command(BaseCommand):
    help = "Создаёт демонстрационных пользователей, проекты, навыки и администратора."

    def handle(self, *args, **options):
        with transaction.atomic():
            skills = self._create_skills()
            users = self._create_users(skills)

            self._create_projects(users, skills)
            self._create_admin()

        self.stdout.write(self.style.SUCCESS("Демо-данные созданы или обновлены."))

    def _create_skills(self) -> dict[str, Skill]:
        skills = {}

        for name in SKILL_NAMES:
            skills[name], _ = Skill.objects.get_or_create(name=name)

        return skills

    def _create_users(self, skills: dict[str, Skill]) -> list[User]:
        users = []

        for user_payload in DEMO_USERS:
            skill_names = user_payload["skills"]
            user_data = {
                key: value
                for key, value in user_payload.items()
                if key != "skills"
            }

            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults=user_data,
            )

            if created or not user.has_usable_password():
                user.set_password(DEMO_PASSWORD)

            for key, value in user_data.items():
                setattr(user, key, value)

            user.save()
            user.skills.set([skills[name] for name in skill_names])
            users.append(user)

        return users

    def _create_projects(self, users: list[User], skills: dict[str, Skill]) -> None:
        projects_payload = [
            {
                "owner": users[0],
                "name": "Сервис поиска pet-проектов",
                "description": "Платформа для поиска команд и быстрых откликов на проекты.",
                "github_url": "https://github.com/anna-demo/teamfinder-demo",
                "status": Project.Status.OPEN,
                "skills": ["Django", "PostgreSQL", "Docker"],
                "participants": [users[1], users[2]],
                "favorites": [users[1]],
            },
            {
                "owner": users[1],
                "name": "Панель аналитики для стартапа",
                "description": "Веб-приложение для визуализации показателей и метрик продукта.",
                "github_url": "https://github.com/misha-demo/analytics-dashboard",
                "status": Project.Status.OPEN,
                "skills": ["React", "UI/UX", "QA"],
                "participants": [users[0]],
                "favorites": [users[0], users[2]],
            },
            {
                "owner": users[2],
                "name": "Инфраструктура для CI/CD",
                "description": "Набор docker-compose и GitHub Actions для учебных pet-проектов.",
                "github_url": "https://github.com/olga-demo/devops-kit",
                "status": Project.Status.CLOSED,
                "skills": ["Docker", "DevOps", "Python"],
                "participants": [users[0], users[1]],
                "favorites": [users[0]],
            },
        ]

        for project_payload in projects_payload:
            self._sync_project(project_payload, skills)

    def _sync_project(
        self,
        project_payload: dict,
        skills: dict[str, Skill],
    ) -> None:
        skill_names = project_payload["skills"]
        participants = project_payload["participants"]
        favorites = project_payload["favorites"]
        owner = project_payload["owner"]

        project_data = {
            key: value
            for key, value in project_payload.items()
            if key not in {"skills", "participants", "favorites", "owner"}
        }

        project, _ = Project.objects.get_or_create(
            owner=owner,
            name=project_data["name"],
            defaults=project_data,
        )

        for key, value in project_data.items():
            setattr(project, key, value)

        project.owner = owner
        project.save()

        # Связи обновляю отдельно, потому что ManyToMany нельзя передать в get_or_create.
        project.skills.set([skills[name] for name in skill_names])
        project.participants.add(owner, *participants)
        project.favorited_by.set(favorites)

    def _create_admin(self) -> None:
        if User.objects.filter(email=ADMIN_EMAIL).exists():
            return

        User.objects.create_superuser(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            name="Admin",
            surname="TeamFinder",
        )