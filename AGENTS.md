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
- Desktop client tests: `cargo test --release` in `desktop/src-tauri` (prepend `%USERPROFILE%\.cargo\bin` to `PATH`).
- Desktop client build: `npm run tauri build` in `desktop/` → NSIS installer under `desktop/src-tauri/target/release/bundle/nsis/`.
- Stop (keep data): `docker compose stop`  |  wipe DB: `docker compose down -v`

## Architecture
- `backend/` is the Django project; `config/` is the settings/urls package plus `views.py` (Dashboard + Reports; there is no `core` app). `manage.py` lives in `backend/`.
- Apps: `users`, `projects`, `tasks`, `comments`, `notifications`, `api` (DRF router/serializers aggregation only).
- Custom user `users.User` (`AUTH_USER_MODEL`) with a `role` field: ADMIN / MANAGER / MEMBER.
- `frontend/` holds templates + static, wired via settings (`TEMPLATES["DIRS"]`, `STATICFILES_DIRS`) — templates are NOT per-app.

## Permissions (role-based, NOT Django groups/permissions)
- `users/permissions.py`: `scope_to_member()`, `IsAdminOrManagerOrReadOnly`, `IsOwnerOrManager`, `IsAdminOrManager`.
- `users/mixins.py`: `ManagerOrAdminRequiredMixin`.
- MEMBER sees only projects/tasks/comments where they are a member; ADMIN/MANAGER see everything; only ADMIN/MANAGER can create/update/delete projects & tasks (web and API).
- API `/api/users/` is ADMIN/MANAGER only (avoids email disclosure to members).

## Security
- New registrations create **inactive** users; activate them from `/admin` (action "Approve selected users (activate)") before they can log in.
- `django-axes` locks out after `AXES_FAILURE_LIMIT` (5) failed logins for `AXES_COOLOFF_MINUTES` (30), by username+IP, returning `429`. It is **disabled automatically during tests** (settings sets `AXES_ENABLED` off when `TESTING`, i.e. `"test" in sys.argv`) — override `AXES_ENABLED=True` if a test needs it.
- `POST /api/token-auth/` is throttled (`DEFAULT_THROTTLE_RATES["token"]`, 10/min). Throttle state lives in the cache; call `cache.clear()` in tests that hit it.
- Session/cookie security is env-driven (`SESSION_COOKIE_AGE`, `SESSION_EXPIRE_AT_BROWSER_CLOSE`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`); secure flags default off for plain-HTTP LAN.
- Password reset uses Django's built-in views under `/accounts/password_reset/…`; it never leaks whether an account exists. Emails go out via SMTP (`EMAIL_*`, Gmail by default); tests override `EMAIL_BACKEND` with `django.core.mail.backends.locmem.EmailBackend` and read `django.core.mail.outbox`.

## Desktop client & remote access (Tailscale)
- End-user usage (three modes: office browser, remote browser over Tailscale, desktop program) is documented in `README.md` → "How to use TaskForge"; install steps for the `.exe` are in `desktop/README.md`.
- `desktop/` is a Tauri v2 Windows client (see `desktop/README.md`). It loads the web app in a WebView2 window and tries a list of server URLs (Tailscale first, then LAN), so one installer works inside and outside the office; it has its own URL test (`cargo test --release` in `desktop/src-tauri`).
- Server URL precedence: runtime `TASKFORGE_SERVER_URL` → `taskforge.json` next to the `.exe` (`server_url` or `server_urls`) → defaults baked at build time from `TASKFORGE_SERVER_URLS` (comma-separated). Real deployment URLs are NOT committed; without the build variable the client falls back to a placeholder.
- Remote access uses `tailscale serve --bg --https=443 http://127.0.0.1:8000`; set `DJANGO_ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` to the `*.ts.net` name. Office clients use the LAN directly (no Tailscale).
- `db` (5432) is bound to `127.0.0.1`; `web` (8000) is published on the LAN. `web` runs `runserver --insecure` so static files work with `DEBUG=0`.
- LAN access is plain HTTP, so `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` stay `0`; Tailscale traffic is still encrypted by WireGuard.
- Building the client needs Rust (installed with `--no-modify-path`, so prepend `%USERPROFILE%\.cargo\bin` to `PATH`) + VS 2022 Build Tools (VCTools workload).

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
- Notifications are created by model signals (`notifications/signals.py`), so they fire from web, API and admin alike. The acting user is read from `notifications/middleware.py:CurrentUserMiddleware` (thread-local) to exclude the actor; without a request the actor is `None`. The bell dropdown shows only **unread** notifications and polls `/notifications/feed/` every 30s (`static/js/notifications.js`); "mark all read" keeps rows in the DB but they stop listing.
- URLs beyond the obvious: global task board `/tasks/`, reports `/reports/`, team `/accounts/team/`, user settings `/accounts/settings/`, notifications `/notifications/`.
