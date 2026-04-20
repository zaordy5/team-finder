from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from projects.models import Project

from .models import User


class BaseStyledFormMixin:
    def _set_common_attrs(self):
        for name, field in self.fields.items():
            widget = field.widget
            widget.attrs.setdefault("id", f"id_{name}")
            if isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "hidden")
            else:
                css_class = widget.attrs.get("class", "").strip()
                widget.attrs["class"] = f"{css_class} form-control".strip()


def validate_github_url(value: str) -> str:
    if not value:
        return ""

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("Ссылка на GitHub должна начинаться с http:// или https://.")

    hostname = (parsed.hostname or "").lower()
    if hostname not in {"github.com", "www.github.com"}:
        raise ValidationError("Ссылка должна вести на GitHub.")
    return value


def normalize_phone(value: str) -> str:
    if not value:
        return ""

    cleaned = value.strip().replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
    if cleaned.startswith("8") and len(cleaned) == 11 and cleaned[1:].isdigit():
        return f"+7{cleaned[1:]}"
    if cleaned.startswith("+7") and len(cleaned) == 12 and cleaned[1:].isdigit():
        return cleaned
    raise ValidationError("Введите номер в формате 8XXXXXXXXXX или +7XXXXXXXXXX.")


class UserRegistrationForm(BaseStyledFormMixin, forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Иван"}),
            "surname": forms.TextInput(attrs={"placeholder": "Иванов"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_common_attrs()

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Имя не может состоять только из пробелов.")
        return name

    def clean_surname(self):
        surname = (self.cleaned_data.get("surname") or "").strip()
        if not surname:
            raise ValidationError("Фамилия не может состоять только из пробелов.")
        return surname

    def clean(self):
        cleaned_data = super().clean()
        email = (cleaned_data.get("email") or "").strip().lower()
        if email:
            cleaned_data["email"] = email
            if User.objects.filter(email=email).exists():
                self.add_error("email", "Пользователь с таким email уже существует.")
        return cleaned_data

    def clean_password(self):
        password = self.cleaned_data.get("password")
        temp_user = User(
            email=(self.data.get("email") or "").strip().lower(),
            name=(self.data.get("name") or "").strip(),
            surname=(self.data.get("surname") or "").strip(),
        )
        password_validation.validate_password(password, user=temp_user)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get("email") or "").strip().lower()
        user.name = self.cleaned_data["name"]
        user.surname = self.cleaned_data["surname"]
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(BaseStyledFormMixin, forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": "Неверный email или пароль.",
        "inactive": "Этот аккаунт отключён.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        self._set_common_attrs()

    def clean(self):
        cleaned_data = super().clean()
        email = (cleaned_data.get("email") or "").strip().lower()
        password = cleaned_data.get("password")
        cleaned_data["email"] = email
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages["invalid_login"])
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages["inactive"])
        return cleaned_data

    def get_user(self):
        return self.user_cache


class UserProfileForm(BaseStyledFormMixin, forms.ModelForm):
    phone = forms.CharField(required=False, max_length=32)

    class Meta:
        model = User
        fields = ("avatar", "name", "surname", "about", "phone", "github_url")
        labels = {
            "avatar": "Аватар",
            "name": "Имя",
            "surname": "Фамилия",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Имя"}),
            "surname": forms.TextInput(attrs={"placeholder": "Фамилия"}),
            "about": forms.Textarea(attrs={"rows": 5, "placeholder": "Расскажите о себе"}),
            "phone": forms.TextInput(attrs={"placeholder": "+7XXXXXXXXXX"}),
            "github_url": forms.URLInput(attrs={"placeholder": "https://github.com/..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_common_attrs()

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Имя не может состоять только из пробелов.")
        return name

    def clean_surname(self):
        surname = (self.cleaned_data.get("surname") or "").strip()
        if not surname:
            raise ValidationError("Фамилия не может состоять только из пробелов.")
        return surname

    def clean_about(self):
        return (self.cleaned_data.get("about") or "").strip()

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone", ""))
        if not phone:
            return None
        queryset = User.objects.filter(phone=phone)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError("Этот номер телефона уже используется.")
        return phone

    def clean_github_url(self):
        return validate_github_url((self.cleaned_data.get("github_url") or "").strip())


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "name", "surname")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AdminUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "name",
            "surname",
            "about",
            "phone",
            "github_url",
            "avatar",
            "skills",
            "is_active",
            "is_staff",
            "is_superuser",
        )


class ProjectForm(BaseStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название",
            "description": "Описание",
            "github_url": "GitHub",
            "status": "Статус",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Название проекта"}),
            "description": forms.Textarea(attrs={"rows": 6, "placeholder": "Кратко опишите проект"}),
            "github_url": forms.URLInput(attrs={"placeholder": "https://github.com/..."}),
            "status": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_common_attrs()

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Название проекта не может состоять только из пробелов.")
        return name

    def clean_description(self):
        return (self.cleaned_data.get("description") or "").strip()

    def clean_github_url(self):
        return validate_github_url((self.cleaned_data.get("github_url") or "").strip())
