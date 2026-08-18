# TeamFinder

`Django / PostgreSQL / Docker`

Web application for finding teammates and organizing collaboration on pet projects.

TeamFinder allows users to create profiles, publish projects, join other teams, save projects to favorites and discover people based on their relationships with projects.

```text
backend       Python / Django
database      PostgreSQL / Django ORM
frontend      Django Templates / HTML / CSS
infrastructure Docker / Docker Compose
ci            GitHub Actions
```

## Features

### Users

- email-based registration and authentication;
- public user profiles;
- profile editing;
- password change;
- paginated user directory;
- project-based user filtering.

### Projects

- project creation and editing;
- project completion workflow;
- paginated project catalog;
- project detail pages;
- team participation;
- favorite projects;
- dedicated favorites page.

### Discovery

Users can be filtered based on their relationships with projects:

- owners of favorite projects;
- owners of projects the current user participates in;
- users interested in the current user's projects;
- participants of the current user's projects.

### Administration

The project includes the standard Django administration interface for managing application data.

## Architecture

The application is split into separate Django apps for users and projects.

```text
team-finder/
├── projects/           project domain and business logic
├── users/              authentication and user profiles
├── team_finder/        Django project configuration
├── static/             static assets
├── media/              uploaded media
├── .github/workflows/  CI configuration
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

Django ORM is used for data access and PostgreSQL is used as the primary database.

## Quick Start

The recommended way to run the application locally is Docker Compose.

### 1. Clone the repository

```bash
git clone https://github.com/zaordy5/team-finder.git
cd team-finder
```

### 2. Prepare environment variables

```bash
cp .env.example .env
```

Review `.env` and adjust the configuration if necessary.

### 3. Start the application

```bash
docker compose up --build
```

After startup, the application is available at:

```text
http://127.0.0.1:8000/projects/list/
```

### 4. Stop the application

```bash
docker compose down
```

To remove the associated Docker volumes as well:

```bash
docker compose down -v
```

## Demo Data

The project includes the `seed_demo` management command that creates demonstration users, projects and relationships between them.

Demo users:

```text
anna@example.com
misha@example.com
olga@example.com
```

Default password for demo users:

```text
Teamfinder123
```

Demo credentials are intended for local development only.

To create an administrator account:

```bash
python manage.py createsuperuser
```

The Django administration interface is available at:

```text
http://127.0.0.1:8000/admin/
```

## Main Routes

```text
/projects/list/         project catalog
/projects/favorites/    favorite projects
/projects/<id>/         project page

/users/list/            user directory
/users/<id>/            user profile
/users/register/        registration
/users/login/           authentication
/users/edit-profile/    profile editing
/users/change-password/ password change

/admin/                 Django administration
```

## Main User Flows

### Project discovery

1. Sign in.
2. Browse the project catalog.
3. Open a project.
4. Add it to favorites or join the team.
5. View related users through project-based filters.

### Project management

1. Create a new project.
2. Edit project information.
3. Manage participation.
4. Complete the project when work is finished.

### User profile

1. Open the personal profile.
2. Update profile information.
3. Browse projects associated with other users.
4. Discover potential teammates.

## Local Development

The project can also run without Docker if PostgreSQL is already available locally.

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Prepare configuration

```bash
cp .env.example .env
```

Configure the PostgreSQL connection in `.env`.

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create demo data

```bash
python manage.py seed_demo
```

### 6. Start the development server

```bash
python manage.py runserver
```

## Development Commands

Create migrations after model changes:

```bash
python manage.py makemigrations
```

Apply migrations:

```bash
python manage.py migrate
```

Validate Django configuration:

```bash
python manage.py check
```

Create an administrator:

```bash
python manage.py createsuperuser
```

## CI

GitHub Actions is used for automated project checks.

Workflow configuration is located in:

```text
.github/workflows/
```

## Tech Stack

```text
Python
Django 5
PostgreSQL
Django ORM
Docker
Docker Compose
GitHub Actions
HTML
CSS
```

## Status

The core application functionality is implemented and the project is maintained as part of my backend development portfolio.
