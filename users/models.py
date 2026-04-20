from io import BytesIO
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.db import models

from .managers import UserManager

USER_NAME_MAX_LENGTH = 124
USER_ABOUT_MAX_LENGTH = 256
USER_PHONE_MAX_LENGTH = 12
AVATAR_IMAGE_SIZE = 256
AVATAR_FONT_SIZE = 110
AVATAR_VERTICAL_OFFSET = 10
AVATAR_COLORS = [
    "#5B8DEF",
    "#6C9E6E",
    "#A57CC1",
    "#C27D5E",
    "#5E9EA0",
    "#D18B47",
]


def _pick_avatar_color(seed: str) -> str:
    if not seed:
        return AVATAR_COLORS[0]
    return AVATAR_COLORS[sum(ord(ch) for ch in seed) % len(AVATAR_COLORS)]


def _generate_avatar_image(letter: str, color: str) -> bytes:
    image = Image.new("RGB", (AVATAR_IMAGE_SIZE, AVATAR_IMAGE_SIZE), color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=AVATAR_FONT_SIZE)
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = (
        (AVATAR_IMAGE_SIZE - text_width) / 2,
        (AVATAR_IMAGE_SIZE - text_height) / 2 - AVATAR_VERTICAL_OFFSET,
    )
    draw.text(position, letter, fill="white", font=font)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class User(AbstractUser):
    username = None
    email = models.EmailField("Email", unique=True)
    name = models.CharField("Имя", max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField("Фамилия", max_length=USER_NAME_MAX_LENGTH)
    about = models.CharField("О себе", max_length=USER_ABOUT_MAX_LENGTH, blank=True)
    phone = models.CharField(
        "Телефон",
        max_length=USER_PHONE_MAX_LENGTH,
        blank=True,
        null=True,
        unique=True,
    )
    github_url = models.URLField("GitHub", blank=True)
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True, null=True)
    skills = models.ManyToManyField(
        "projects.Skill",
        verbose_name="Навыки",
        related_name="users",
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        full_name = f"{self.name} {self.surname}".strip()
        return full_name or self.email

    def get_absolute_url(self):
        return f"/users/{self.pk}/"

    def _ensure_avatar(self):
        if self.avatar:
            return
        initial = (self.name[:1] or self.email[:1] or "?").upper()
        color = _pick_avatar_color(self.email or self.name)
        image_content = _generate_avatar_image(initial, color)
        filename = f"avatar_{uuid4()}.png"
        self.avatar.save(filename, ContentFile(image_content), save=False)

    def save(self, *args, **kwargs):
        self._ensure_avatar()
        super().save(*args, **kwargs)
