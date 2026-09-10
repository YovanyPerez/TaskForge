# TaskForge — Architecture

Project & task management platform (simplified Jira/Trello). Server-rendered
Django app plus a REST API, packaged with Docker.

## Technology stack

- **Backend**: Python 3.12, Django 5.2 LTS, Django REST Framework
- **Database**: PostgreSQL 16 (psycopg 3)
- **Frontend**: Django Templates, Bootstrap 5 (CDN), vanilla JavaScript
- **Infra**: Docker, Docker Compose
- **Auth**: Django auth (custom User) + DRF SessionAuth + TokenAuth
- **Testing**: Django built-in test runner

## Repository layout

```
taskforge/
├── backend/                 # Django project
│   ├── manage.py
│   ├── config/              # settings, urls, asgi, wsgi, dashboard view
│   ├── users/               # custom User, roles, auth, permissions
│   ├── projects/            # Project model + web/API views
│   ├── tasks/               # Task model + web/API views
│   ├── comments/            # Comment model + web/API views
│   └── api/                 # DRF router + token-auth endpoint
├── frontend/
│   ├── templates/           # base.html, dashboard, per-app pages
│   └── static/              # css, js, images
├── docker-compose.yml       # web + db services
├── Dockerfile
├── requirements.txt
└── .env.example             # template for the (git-ignored) .env
```

## Applications & responsibilities

| App | Responsibility |
| --- | --- |
| `users` | Custom `User` (AbstractUser + `role`), auth views (register/login/profile), role mixins & DRF permissions, token auto-creation signal |
| `projects` | `Project` model, CRUD web views, DRF viewset |
| `tasks` | `Task` model, CRUD web views, DRF viewset, `TaskForm` (assignment limited to project members) |
| `comments` | `Comment` model, create/delete web views, DRF viewset |
| `api` | Aggregates all viewsets into a `DefaultRouter`, hosts `POST /api/token-auth/` |

## Data model

- **User** (`users.User`, `AUTH_USER_MODEL`): `AbstractUser` + `role`
  (ADMIN / MANAGER / MEMBER), `created_at`, `updated_at`.
- **Project**: name, description, `start_date`, `end_date`, `status`
  (PLANNING / IN_PROGRESS / COMPLETED / ON_HOLD), `created_by` (FK),
  `members` (M2M User), timestamps.
- **Task**: title, description, `project` (FK), `assigned_to` (FK User, nullable),
  `priority` (LOW / MEDIUM / HIGH), `status` (TODO / IN_PROGRESS / DONE),
  `due_date`, `created_by` (FK), timestamps.
- **Comment**: `task` (FK), `user` (FK), content, timestamps.

Relationships: `Project 1—N Task`, `Task 1—N Comment`, `User M—N Project`
(members), plus `created_by` / `assigned_to` FKs to `User`. Deletes cascade:
project -> tasks -> comments.

## URL structure

```
/                          dashboard (config.views.DashboardView)
/accounts/                 login, logout, register, profile
/projects/                 list, new, <id>, <id>/edit, <id>/delete
/projects/<id>/tasks/      list, new, <id>, <id>/edit, <id>/delete
/projects/<id>/tasks/<tid>/comments/   add, <id>/delete
/api/                      DRF router (users, projects, tasks, comments)
/api/token-auth/           obtain an auth token
/admin/                    Django admin (all models registered)
```

## Authorization model

Authorization is **role-based** (not Django groups/permissions). The `role`
field on `User` is the single source of truth.

- **Read visibility** (`scope_to_member`): MEMBER sees only the projects they
  belong to (and their tasks/comments); ADMIN/MANAGER see everything.
- **Write** (`ManagerOrAdminRequiredMixin` web, `IsAdminOrManagerOrReadOnly`
  API): only ADMIN/MANAGER create/update/delete projects & tasks.
- **Comments**: any project member can add; only the author or ADMIN/MANAGER
  can modify/delete (`IsOwnerOrManager`).
- **API users**: read-only (`ReadOnlyModelViewSet`) — user/role management
  happens in the web app / admin.

Visibility scoping is enforced in both the web views (`get_queryset`) and the
API viewsets (`get_queryset` + `perform_create`), plus the dashboard queries.

## Authentication

- **Web / browsable API**: Django session (`SessionAuthentication`).
- **Programmatic**: DRF `TokenAuthentication`. Tokens are auto-created on user
  creation (`users/signals.py`) and can be obtained via `POST /api/token-auth/`
  with username + password.

## Configuration & environment

All configuration comes from environment variables (no hardcoded secrets).
`docker-compose.yml` interpolates values from the git-ignored `.env`
(see `.env.example`). `settings.py` reads `os.environ` directly; the DB engine
is PostgreSQL with `psycopg`.

## Development & operations

- `docker compose up -d` builds (first run) and starts `web` + `db`; the `web`
  container runs `migrate` then `runserver` on startup.
- Code changes are picked up live via the `.:/app` bind mount; rebuild only
  after changing `requirements.txt`/`Dockerfile`.
- Database data persists in the `postgres_data` volume; `docker compose down -v`
  wipes it.

## Testing

Django's built-in runner, tests colocated per app under `*/tests/`
(`test_models.py`, `test_views.py`, `test_forms.py`, and `api/tests/test_api.py`).
Run with:

```bash
docker compose run --rm web python manage.py test
```
