from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailBackend(ModelBackend):
    def authenticate(
        self,
        request,
        username=None,
        password=None,
        email=None,
        **kwargs,
    ):
        login_email = email or username

        if not login_email or not password:
            return None

        try:
            user = User.objects.get(email__iexact=login_email)
        except User.DoesNotExist:
            return None

        # Проверяем и пароль, и возможность входа для пользователя.
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None