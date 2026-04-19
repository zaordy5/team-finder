# TeamFinder

Итоговый Django-проект для поиска команды и совместной работы над pet-проектами.

Проект зафиксирован **вариант 1**: избранные проекты и фильтрация пользователей. 

## Что реализовано

- регистрация и вход по email;
- публичные профили пользователей;
- редактирование профиля и смена пароля;
- список пользователей с пагинацией по 12 карточек;
- список проектов с пагинацией по 12 карточек;
- создание, редактирование и завершение проекта;
- участие в чужих проектах;
- добавление проектов в избранное и отдельная страница избранного;
- PostgreSQL и запуск через Docker Compose;
- демонстрационные данные;
- админ-панель Django;
- автотесты.

## Быстрый запуск

### 1. Подготовить `.env`

```bash
cp .env_example .env
```

### 2. Запустить проект

```bash
docker compose up --build
```

После запуска проект будет доступен по адресу:

```text
http://127.0.0.1:8000/projects/list/
```

### 3. Остановить проект

```bash
docker compose down
```

Если нужно остановить и удалить volumes:

```bash
docker compose down -v
```

## Тестовые аккаунты

После первого запуска автоматически создаются тестовые пользователи и проекты.

Пароль для обычных пользователей:

```text
Teamfinder123
```

Обычные аккаунты:

- `anna@example.com`
- `misha@example.com`
- `olga@example.com`

Админ-панель:

```text
http://127.0.0.1:8000/admin/
```

Данные администратора:

- email: `admin@teamfinder.local`
- пароль: `Admin12345`

### Основные страницы

- главная страница: `/projects/list/`
- список пользователей: `/users/list/`
- страница избранного: `/projects/favorites/`
- страница пользователя: `/users/<id>/`
- страница проекта: `/projects/<id>/`
- регистрация: `/users/register/`
- вход: `/users/login/`
- редактирование профиля: `/users/edit-profile/`
- смена пароля: `/users/change-password/`

### Основной сценарий проверки (вариант 1)

1. Войти под `anna@example.com` / `Teamfinder123`.
2. Открыть `/projects/list/`.
3. Добавить любой чужой проект в избранное.
4. Открыть `/projects/favorites/` и проверить, что проект появился.
5. Открыть чужой проект и присоединиться к нему.
6. Открыть `/users/list/` и проверить 4 фильтра:
   - `owners-of-favorite-projects`
   - `owners-of-participating-projects`
   - `interested-in-my-projects`
   - `participants-of-my-projects`
7. Открыть свой профиль и проверить редактирование профиля.
8. Создать новый проект.
9. Отредактировать созданный проект.
10. Завершить созданный проект.
11. Проверить `/admin/`.

## Локальный запуск без Docker

### 1. Создать виртуальное окружение

```bash
python -m venv .venv
```

На Windows:

```bash
.venv\Scripts\activate
```

На Linux/macOS:

```bash
source .venv/bin/activate
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Подготовить `.env`

```bash
cp .env_example .env
```

Если PostgreSQL запускается локально вне Docker, укажите свои параметры подключения.

### 4. Применить миграции и создать демо-данные

```bash
python manage.py migrate
python manage.py seed_demo
```

### 5. Запустить сервер

```bash
python manage.py runserver
```

## Полезные команды

Проверка тестов в Docker:

```bash
docker compose exec web python manage.py test
```

Создание миграций:

```bash
python manage.py makemigrations
```

## Технические детали

- Framework: Django 5
- Database: PostgreSQL
- Containerization: Docker Compose
- Хранение данных БД: volume `postgres_data`
- Хранение медиафайлов: volume `media_data`
