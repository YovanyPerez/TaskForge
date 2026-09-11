# TaskForge — Architecture

Project & task management platform (simplified Jira/Trello). Server-rendered
Django app plus a REST API, packaged with Docker. English/Spanish UI and an
in-app notification bell.

## Technology stack

- **Backend**: Python 3.12, Django 5.2 LTS, Django REST Framework
- **Database**: PostgreSQL 16 (psycopg 3)
- **Frontend**: Django Templates, Bootstrap 5 (CDN), vanilla JavaScript
- **Infra**: Docker, Docker Compose
- **Auth**: Django auth (custom User) + DRF SessionAuth + TokenAuth
- **Security**: `django-axes` brute-force lockout, DRF throttling, approval-gated registration
- **i18n**: Django i18n (`gettext`), English + Spanish
- **Testing**: Django built-in test runner

## Repository layout

```
taskforge/
├── backend/                 # Django project
│   ├── manage.py
│   ├── config/              # settings, urls, asgi/wsgi, views (Dashboard, Reports)
│   ├── users/               # custom User, roles, auth, permissions, settings, team
│   ├── projects/            # Project model + web/API views + members
│   ├── tasks/               # Task model + web/API views + global board
│   ├── comments/            # Comment model + web/API views
│   ├── notifications/       # Notification model, signals, bell feed
│   └── api/                 # DRF router + token-auth endpoint
├── frontend/
│   ├── templates/           # base.html, partials, per-app pages
│   └── static/              # css (main/components/responsive), js, images
├── desktop/                 # Tauri v2 desktop client (Windows)
│   ├── src-tauri/           # Rust shell + tauri.conf.json
│   └── ui/                  # local offline page
├── locale/es/LC_MESSAGES/   # Spanish translation catalog (.po/.mo)
├── docker-compose.yml       # web + db services
├── Dockerfile
├── requirements.txt
├── .env.example             # template for the (git-ignored) .env
├── AGENTS.md                # agent/onboarding notes
└── architecture.md          # this file
```

## Applications & responsibilities

| App | Responsibility |
| --- | --- |
| `users` | Custom `User` (AbstractUser + `role` + `language`), auth views (register/login/logout/profile/settings) + email password reset, team directory, role mixins & DRF permissions, token auto-creation signal, per-request language middleware |
| `projects` | `Project` model, CRUD web views, member add/remove, DRF viewset |
| `tasks` | `Task` model, CRUD web views, per-project board + global board, assignee status change, DRF viewset |
| `comments` | `Comment` model, create/delete web views, DRF viewset |
| `notifications` | `Notification` model, signal-driven creation, actor thread-local, bell feed/mark-read views |
| `api` | Aggregates all viewsets into a `DefaultRouter`, hosts `POST /api/token-auth/` |
| `config` | Project settings/urls and `views.py` (Dashboard, Reports — no separate `core` app) |

## Data model

- **User** (`users.User`, `AUTH_USER_MODEL`): `AbstractUser` + `role`
  (ADMIN / MANAGER / MEMBER), `language` (en/es, blank = default),
  `created_at`, `updated_at`.
- **Project**: name, description, `start_date`, `end_date`, `status`
  (PLANNING / IN_PROGRESS / COMPLETED / ON_HOLD), `created_by` (FK),
  `members` (M2M User), timestamps. `clean()` rejects `end_date < start_date`.
- **Task**: title, description, `project` (FK), `assigned_to` (FK User, nullable),
  `priority` (LOW / MEDIUM / HIGH), `status` (TODO / IN_PROGRESS / DONE),
  `due_date`, `created_by` (FK), timestamps.
- **Comment**: `task` (FK), `user` (FK), content, timestamps.
- **Notification**: `recipient` (FK), `actor` (FK, nullable), `verb`
  (TASK_ASSIGNED / PROJECT_MEMBER_ADDED / TASK_COMPLETED / PROJECT_COMPLETED),
  `project` / `task` (nullable FKs), `is_read`, `created_at`.

Relationships: `Project 1—N Task`, `Task 1—N Comment`, `User M—N Project`
(members), plus `created_by` / `assigned_to` FKs to `User`. Deletes cascade:
project -> tasks -> comments, and project/task -> notifications.

## URL structure

```
/                          dashboard (config.views.DashboardView)
/accounts/                 login, logout, register, profile
/accounts/password_reset/  request reset; /done/, /reset/<uidb64>/<token>/, /reset/done/
/accounts/settings/        language + appearance
/accounts/team/            team directory (+ /<id>/ member detail)
/tasks/                    global task board (all visible tasks)
/reports/                  aggregate reports
/projects/                 list, new, <id>, <id>/edit, <id>/delete
/projects/<id>/members/    add, <user_id>/remove (POST)
/projects/<id>/tasks/      list, new, <id>, <id>/edit, <id>/delete, <id>/status
/projects/<id>/tasks/<tid>/comments/   add, <id>/delete
/notifications/            feed (JSON), read-all, <id>/read
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
- **Task status**: the assignee (or ADMIN/MANAGER) may change only the status
  (`tasks:status`).
- **Project members**: ADMIN/MANAGER add/remove members.
- **Comments**: any project member can add; only the author or ADMIN/MANAGER
  can modify/delete (`IsOwnerOrManager`).
- **API users**: read-only (`ReadOnlyModelViewSet`) and restricted to
  ADMIN/MANAGER (`IsAdminOrManager`) — user/role management happens in the web
  app / admin.
- **Registration**: open sign-up creates an **inactive** account; an ADMIN must
  activate it from `/admin` before the user can log in.

Visibility scoping is enforced in both the web views (`get_queryset`) and the
API viewsets (`get_queryset` + `perform_create`), plus the dashboard, reports,
team, and notification queries.

## Security hardening

- **Brute-force lockout**: `django-axes` locks by username+IP after 5 failures
  for 30 minutes (`AXES_*` settings, `429` response). It covers web login,
  `/admin` and the DRF token endpoint (which calls `authenticate`). Disabled
  during the test run (`AXES_ENABLED` is off when `manage.py test` runs).
  Unlock from `/admin` (axes models) or the `axes_reset` command.
- **API throttling**: `POST /api/token-auth/` is rate-limited per IP
  (`DEFAULT_THROTTLE_RATES["token"]`, 10/min).
- **Sessions/cookies**: `SESSION_COOKIE_AGE` (default 8h),
  `SESSION_EXPIRE_AT_BROWSER_CLOSE`, `SESSION_COOKIE_SECURE` and
  `CSRF_COOKIE_SECURE` are env-driven (secure flags default off for plain-HTTP
  LAN, enable them over HTTPS). `SESSION_COOKIE_SAMESITE` is `Lax`.
- **Email/password**: password reset does not leak account existence; inactive
  accounts are ignored by the reset form.
- Secrets live only in the git-ignored `.env` (never committed).

## Authentication

- **Web / browsable API**: Django session (`SessionAuthentication`).
- **Programmatic**: DRF `TokenAuthentication`. Tokens are auto-created on user
  creation (`users/signals.py`) and can be obtained via `POST /api/token-auth/`
  with username + password (rate-limited).
- **Password reset**: Django's built-in views send a single-use link over SMTP
  (`EMAIL_*`, Gmail by default; `POST /api/token-auth/`-independent). The form
  always redirects to "check your email", so it never reveals whether an address
  exists; inactive users are skipped. Templates live in `frontend/templates/users/`.

## Notifications

Created by **model signals** (`notifications/signals.py`), so they fire from
web, API and admin alike:

- task `assigned_to` changes -> assignee is notified;
- user added to `Project.members` (m2m `post_add`) -> member is notified;
- task `status` becomes DONE -> creator + project members;
- project `status` becomes COMPLETED -> project members.

The acting user is read from a thread-local set by
`notifications/middleware.py:CurrentUserMiddleware` (excluded from recipients);
without an HTTP request the actor is `None`. The bell dropdown (topbar) shows
only **unread** items and polls `GET /notifications/feed/` every 30s via
`static/js/notifications.js`; a context processor supplies the count/list for
the initial render. "Mark all read" sets `is_read=True` (rows are kept in the
DB) so the panel empties.

## Internationalization

- Strings wrapped with `{% trans %}`/`{% blocktrans %}` (templates) and
  `gettext(_lazy)` (models, forms, validators, permissions, views).
- Per-user preference stored in `User.language`; activated per request by
  `users/middleware.py:UserLanguageMiddleware`. The sidebar language switcher
  (`users:switch-language`) also sets Django's `django_language` cookie for
  anonymous visitors.
- Catalog at repo-root `locale/` (`LOCALE_PATHS`); regenerate with
  `makemessages -l es` run from `/app`, translate, then `compilemessages`.

## Settings & appearance

`users:settings` hosts language selection (server-side) and appearance options
(accent color, density) stored in `localStorage` and applied by
`static/js/appearance.js` via CSS variables.

## Desktop client (Windows)

`desktop/` is an optional Tauri v2 shell that opens the web app in a native
WebView2 window instead of a browser. It does not reimplement any UI: it tries a
list of candidate server URLs (default: Tailscale name, then LAN hostname/IP;
overridable via `TASKFORGE_SERVER_URL` or a `taskforge.json` next to the `.exe`)
and uses the first one that responds. If none respond it shows a local offline
page with a retry action. Session cookies persist in the WebView2 profile, so
users stay logged in. Built with `npm run tauri build`; the web app remains
fully usable in a browser.

## Configuration & environment

All configuration comes from environment variables (no hardcoded secrets).
`docker-compose.yml` interpolates values from the git-ignored `.env`
(see `.env.example`) and forwards them into the `web` container. `settings.py`
reads `os.environ` directly; the DB engine is PostgreSQL with `psycopg`.

Groups: `DATABASE_*` (Postgres), `EMAIL_*` + `DEFAULT_FROM_EMAIL` (SMTP for
password reset), `SESSION_COOKIE_*` / `CSRF_*` (session & CSRF hardening),
`AXES_*` (brute-force policy) and `CSRF_TRUSTED_ORIGINS` (Tailscale hostname).

## Development & operations

- `docker compose up -d` builds (first run) and starts `web` + `db`; the `web`
  container runs `migrate` then `runserver --insecure` on startup (`--insecure`
  serves static files with `DEBUG=0`). `db` is bound to `127.0.0.1`; `web` is
  published on the LAN and also exposed remotely via `tailscale serve`.
- Code changes are picked up live via the `.:/app` bind mount; rebuild only
  after changing `requirements.txt`/`Dockerfile` (the image installs `gettext`).
- Database data persists in the `postgres_data` volume; `docker compose down -v`
  wipes it.

## Testing

Django's built-in runner, tests colocated per app under `*/tests/`
(`test_models.py`, `test_views.py`, `test_forms.py`, and feature-specific files).
Run with:

```bash
docker compose run --rm web python manage.py test
```

The desktop client has its own Rust tests (`cargo test --release` in
`desktop/src-tauri`, covering URL parsing and the candidate URLs).
