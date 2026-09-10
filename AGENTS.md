# AGENTS.md

## Setup / environment
- Everything runs via Docker. On this machine the Docker daemon does NOT auto-start — open Docker Desktop first.
- Local Python is 3.11 but the app runs on Python 3.12 inside the container. Never run `python manage.py` locally; always `docker compose run --rm web ...`.
- `.env` is required but git-ignored. Create it from `.env.example` (`cp .env.example .env`); `docker-compose.yml` interpolates `${...}` from it.
- `web` bind-mounts `.` -> `/app`, so code edits are live. Rebuild only after changing `requirements.txt`/`Dockerfile`.

## Commands
- Start: `docker compose up -d`  (runs `migrate` automatically on boot)
- Any manage.py command: `docker compose run --rm web python manage.py <cmd>`
- Run all tests: `docker compose run --rm web python manage.py test`  (Django built-in runner, NOT pytest)
- Single test: `docker compose run --rm web python manage.py test projects.tests.test_views.ProjectCrudTests.test_list`
- Fast sanity gate: `docker compose run --rm web python manage.py check`
- Stop (keep data): `docker compose stop`  |  wipe DB: `docker compose down -v`

## Architecture
- `backend/` is the Django project; `config/` is the settings/urls package (there is no `core` app). `manage.py` lives in `backend/`.
- Apps: `users`, `projects`, `tasks`, `comments`, `api` (DRF router/serializers aggregation only).
- Custom user `users.User` (`AUTH_USER_MODEL`) with a `role` field: ADMIN / MANAGER / MEMBER.
- `frontend/` holds templates + static, wired via settings (`TEMPLATES["DIRS"]`, `STATICFILES_DIRS`) — templates are NOT per-app.

## Permissions (role-based, NOT Django groups/permissions)
- `users/permissions.py`: `scope_to_member()`, `IsAdminOrManagerOrReadOnly`, `IsOwnerOrManager`.
- `users/mixins.py`: `ManagerOrAdminRequiredMixin`.
- MEMBER sees only projects/tasks/comments where they are a member; ADMIN/MANAGER see everything; only ADMIN/MANAGER can create/update/delete projects & tasks (web and API).

## i18n (English/Español)
- Strings: `{% trans %}`/`{% blocktrans %}` in templates, `gettext_lazy` in
  models/forms/validators/permissions. Every new user-facing string must be wrapped.
- Preference: `User.language` field, activated per request by
  `users/middleware.py:UserLanguageMiddleware`.
- Catalog lives at repo-root `locale/` (`LOCALE_PATHS`). Regenerate from `/app`
  (NOT `backend/`, templates live in `frontend/`):
  `docker compose run --rm -w /app web python backend/manage.py makemessages -l es --ignore=.git --ignore=staticfiles`,
  then fill `msgstr`, then `compilemessages`. Rebuild the image after
  `Dockerfile` changes (`gettext` system package is required).

## Gotchas
- `createsuperuser` leaves `role=MEMBER`; `is_superuser` grants nothing in-app. Set Role=Admin in `/admin` to actually create projects.
- Tests live per-app (`users/tests/`, `projects/tests/`, ...), not in a top-level `tests/` dir (Django default discovery).
- DRF 3.18 returns `403` (not `401`) for unauthenticated session requests — assert `in (401, 403)`, not `== 401`.
- API token auth: `POST /api/token-auth/` (username+password); tokens are auto-created via `users/signals.py`.
- Adding an app with bundled migrations (e.g. `rest_framework.authtoken`) still requires a `manage.py migrate`.
