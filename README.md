# TaskForge

Project & Task Management Platform — a lightweight, self-hosted project and task
management system inspired by simplified versions of Jira and Trello.

## Features (planned)

- **Users & roles**: `ADMIN`, `MANAGER`, `MEMBER` with Django's built-in auth.
- **Projects**: create, track status (`Planning`, `In Progress`, `Completed`, `On Hold`), and manage members.
- **Tasks**: create, assign, prioritize, and track status (`To Do`, `In Progress`, `Done`).
- **Comments**: discuss tasks.
- **Dashboard**: overview of projects and tasks.
- **REST API**: JSON API for all resources.
- **Permissions & security**: role-based access control.
- **Settings**: interface language (English/Español) persisted per user, plus
  browser-local appearance options (accent color, density).

> Status: **Phases 1–9 complete** (foundation + auth + projects/tasks/comments
> CRUD + dashboard + REST API + permissions/security + testing), plus extras:
> global tasks board, team directory, reports, and Settings (i18n + appearance).
> UI/UX polish (Phase 10) remains.

## Technology stack

- **Backend**: Python 3.12, Django 5.2 LTS, Django REST Framework
- **Database**: PostgreSQL 16
- **Frontend**: Django Templates, Bootstrap 5 (CDN), vanilla JavaScript
- **Development**: Docker, Docker Compose, Git
- **Testing**: Django's built-in test runner

## Architecture

The project is split into a `backend/` (Django project) and a `frontend/`
(templates + static) directory, kept separate so the frontend can later evolve
into a standalone SPA without touching the backend.

```
backend/
  config/      Django project settings, urls, wsgi/asgi
  users/       Custom User model (AbstractUser) + roles
  projects/    Project model
  tasks/       Task model
  comments/    Comment model
  api/         DRF foundation (endpoints added in Phase 7)

frontend/
  templates/   Django templates (base.html, home.html)
  static/      css, js, images
```

Each domain app owns its models, admin registration, and its own tests.

## Folder structure

```
taskforge/
├── backend/
│   ├── manage.py
│   ├── config/            # settings, urls, asgi, wsgi
│   ├── users/             # custom User model
│   ├── projects/
│   ├── tasks/
│   ├── comments/
│   └── api/               # DRF foundation
├── frontend/
│   ├── templates/
│   └── static/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Requirements

- Docker (with Docker Compose v2)

Nothing else is required locally — everything runs in containers.

## Environment configuration

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set a real `SECRET_KEY` (any long random string is fine for
   development). The database values are used by Docker Compose and are
   already configured for local development.

`.env` is git-ignored and must never be committed.

## Docker setup

Build and start the full stack:

```bash
docker compose up
```

This starts the Django application and PostgreSQL database. On first run the
Dockerfile builds the image (this may take a few minutes).

- Django: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- PostgreSQL: `localhost:5432` (mapped via `DATABASE_PORT`)

Stop the stack with `Ctrl+C`, or `docker compose down` to remove containers.
The database persists in the `postgres_data` Docker volume; use
`docker compose down -v` to wipe it.

## Database setup

PostgreSQL is provisioned automatically by Docker Compose using the values in
`.env`. No manual setup is required.

## Migration commands

Migrations run automatically when the `web` container starts. To run them
manually:

```bash
docker compose run --rm web python manage.py makemigrations
docker compose run --rm web python manage.py migrate
```

## Create a superuser

```bash
docker compose run --rm web python manage.py createsuperuser
```

Follow the prompts, then sign in at http://localhost:8000/admin.

## Start the project

```bash
docker compose up
```

## REST API

The API is served under `/api/` (Django REST Framework) and requires
authentication (`SessionAuthentication`, same session as the web app). A
browsable API is available when logged in.

| Endpoint | Methods |
| --- | --- |
| `/api/users/` | `GET`, `GET /api/users/<id>/` (read-only) |
| `/api/projects/` | `GET`, `POST` |
| `/api/projects/<id>/` | `GET`, `PUT`, `PATCH`, `DELETE` |
| `/api/tasks/` | `GET`, `POST` |
| `/api/tasks/<id>/` | `GET`, `PUT`, `PATCH`, `DELETE` |
| `/api/comments/` | `GET`, `POST` |
| `/api/comments/<id>/` | `GET`, `PUT`, `PATCH`, `DELETE` |

### Authentication

- **Session**: same session as the web app (browsable API).
- **Token**: obtain a token with `POST /api/token-auth/` (username + password),
  then send it as `Authorization: Token <key>`.

### Permissions

- `MEMBER` sees only projects/tasks/comments where they are a member.
- `ADMIN`/`MANAGER` see everything and are the only roles that can create,
  update, or delete projects and tasks via the API.
- Comments can be created by any project member; only the author or an
  `ADMIN`/`MANAGER` can modify or delete a comment.

## Run tests

```bash
docker compose run --rm web python manage.py test
```
