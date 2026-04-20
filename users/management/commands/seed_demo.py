from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project, Skill
from users.models import User


class Command(BaseCommand):
    help = "Создаёт демонстрационных пользователей, проекты, навыки и администратора."

    def handle(self, *args, **options):
        with transaction.atomic():
            skills = {}
            for name in [
                "Django",
                "PostgreSQL",
                "Docker",
                "React",
                "Python",
                "UI/UX",
                "DevOps",
                "QA",
            ]:
                skills[name], _ = Skill.objects.get_or_create(name=name)

            demo_users = [
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

            created_users = []
            for item in demo_users:
                skill_names = item.pop("skills")
                user, created = User.objects.get_or_create(
                    email=item["email"],
                    defaults=item,
                )
                if created or not user.has_usable_password():
                    user.set_password("Teamfinder123")
                for key, value in item.items():
                    setattr(user, key, value)
                user.save()
                user.skills.set([skills[name] for name in skill_names])
                created_users.append(user)

            projects_payload = [
                {
                    "owner": created_users[0],
                    "name": "Сервис поиска pet-проектов",
                    "description": "Платформа для поиска команд и быстрых откликов на проекты.",
                    "github_url": "https://github.com/anna-demo/teamfinder-demo",
                    "status": Project.Status.OPEN,
                    "skills": ["Django", "PostgreSQL", "Docker"],
                    "participants": [created_users[1], created_users[2]],
                    "favorites": [created_users[1]],
                },
                {
                    "owner": created_users[1],
                    "name": "Панель аналитики для стартапа",
                    "description": "Веб-приложение для визуализации показателей и метрик продукта.",
                    "github_url": "https://github.com/misha-demo/analytics-dashboard",
                    "status": Project.Status.OPEN,
                    "skills": ["React", "UI/UX", "QA"],
                    "participants": [created_users[0]],
                    "favorites": [created_users[0], created_users[2]],
                },
                {
                    "owner": created_users[2],
                    "name": "Инфраструктура для CI/CD",
                    "description": "Набор docker-compose и GitHub Actions для учебных pet-проектов.",
                    "github_url": "https://github.com/olga-demo/devops-kit",
                    "status": Project.Status.CLOSED,
                    "skills": ["Docker", "DevOps", "Python"],
                    "participants": [created_users[0], created_users[1]],
                    "favorites": [created_users[0]],
                },
            ]

            for payload in projects_payload:
                skill_names = payload.pop("skills")
                participants = payload.pop("participants")
                favorites = payload.pop("favorites")
                owner = payload.pop("owner")
                project, _ = Project.objects.get_or_create(
                    owner=owner,
                    name=payload["name"],
                    defaults=payload,
                )
                for key, value in payload.items():
                    setattr(project, key, value)
                project.owner = owner
                project.save()
                project.skills.set([skills[name] for name in skill_names])
                project.participants.add(owner, *participants)
                project.favorited_by.set(favorites)

            admin_email = "admin@teamfinder.local"
            if not User.objects.filter(email=admin_email).exists():
                User.objects.create_superuser(
                    email=admin_email,
                    password="Admin12345",
                    name="Admin",
                    surname="TeamFinder",
                )

        self.stdout.write(self.style.SUCCESS("Демо-данные созданы или обновлены."))
