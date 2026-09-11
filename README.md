# TaskForge

Project & Task Management Platform — a lightweight, self-hosted project and task
management system inspired by simplified versions of Jira and Trello.

## Features

- **Users & roles**: `ADMIN`, `MANAGER`, `MEMBER` with Django's built-in auth.
  Sign-up creates an **inactive** account until an admin approves it.
- **Projects**: create, track status (`Planning`, `In Progress`, `Completed`, `On Hold`), and manage members.
- **Tasks**: create, assign, prioritize, and track status (`To Do`, `In Progress`, `Done`).
- **Comments**: discuss tasks.
- **Dashboard & Reports**: overview of projects, tasks, workload and overdue items.
- **Global task board** and **team directory**.
- **Notifications**: bell with unread counter — alerts when you are assigned a
  task, added to a project, or when a task/project is completed.
- **Password reset**: email-based reset link (Gmail SMTP), without leaking
  whether an account exists.
- **Security**: role-based access control, `django-axes` brute-force lockout,
  API throttling, approval-gated registration, env-driven session/cookies.
- **Desktop client**: optional Windows app (Tauri/WebView2) that works on the
  LAN and from outside over Tailscale.
- **REST API**: JSON API for all resources.
- **Settings**: interface language (English/Español) persisted per user, plus
  browser-local appearance options (accent color, density).

> Status: feature-complete for internal use — auth (+ password reset), projects,
> tasks, comments, dashboard, reports, REST API, permissions & security,
> notifications, i18n and the desktop client are done. UI/UX polish remains.

## How to use TaskForge

There are three ways to use it. All of them need the **server** (the PC running
Docker) turned on with the stack up; the desktop program and remote access also
need **Tailscale** connected.

1. **Office — any browser (nothing to install):**
   open `http://<server-host>:8000` (or `http://<server-ip>:8000`) and log in.
2. **From home — any browser (Tailscale):**
   connect Tailscale, open `https://<machine>.<tailnet>.ts.net` and log in.
3. **Desktop program (.exe):**
   install `TaskForge_0.1.0_x64-setup.exe` once (see
   [desktop/README.md](desktop/README.md)), then open **TaskForge** from the
   Start menu. The same program works in the office and from home: it tries the
   Tailscale name first and the LAN next, using the first one that responds. If
   none respond it shows a **Retry** screen asking you to check the network/VPN.

The real deployment URLs are not committed: they live in your `.env` (server)
and are baked into the client at build time (see `desktop/README.md`).

New accounts must be approved by an admin before the first login (see
[Accounts & password reset](#accounts--password-reset)).

## Technology stack

- **Backend**: Python 3.12, Django 5.2 LTS, Django REST Framework
- **Database**: PostgreSQL 16
- **Frontend**: Django Templates, Bootstrap 5 (CDN), vanilla JavaScript
- **Security**: `django-axes` (brute-force lockout), DRF throttling
- **Desktop client**: Tauri v2 (Rust) + WebView2, optional and Windows-only
- **Remote access**: Tailscale (`tailscale serve`, HTTPS)
- **Development**: Docker, Docker Compose, Git
- **Testing**: Django's built-in test runner (+ `cargo test` for the client)

## Architecture

The project is split into a `backend/` (Django project), a `frontend/`
(templates + static) and an optional `desktop/` (Tauri client). The frontend is
server-rendered and kept separate from the backend so it can evolve
independently.

```
backend/
  config/        Django project settings, urls, wsgi/asgi, views
  users/         Custom User model (AbstractUser) + roles, auth, password reset
  projects/      Project model + members
  tasks/         Task model + boards
  comments/      Comment model
  notifications/ Notification model + signals + bell feed
  api/           DRF router + token-auth endpoint

frontend/
  templates/     Django templates (base.html, partials, per-app pages)
  static/        css, js, images

desktop/         Optional Tauri v2 Windows client (Rust + WebView2)
  src-tauri/     Rust shell + tauri.conf.json
  ui/            Local "no connection" page
```

Each domain app owns its models, admin registration, and its own tests.

## Folder structure

```
taskforge/
├── backend/
│   ├── manage.py
│   ├── config/            # settings, urls, asgi, wsgi, dashboard/reports views
│   ├── users/             # custom User, roles, auth, permissions, team
│   ├── projects/
│   ├── tasks/
│   ├── comments/
│   ├── notifications/
│   └── api/               # DRF router + token-auth
├── frontend/
│   ├── templates/
│   └── static/
├── desktop/               # optional Tauri v2 Windows client
├── locale/                # Spanish translation catalog
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── AGENTS.md
├── architecture.md
└── README.md
```

## Requirements

- Docker (with Docker Compose v2)

Nothing else is required locally to run the server — everything runs in
containers. Building the optional desktop client additionally needs Node, Rust
and VS Build Tools (see `desktop/README.md`).

## Environment configuration

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set a real `SECRET_KEY` (any long random string is fine for
   development). The database values are used by Docker Compose and are
   already configured for local development.

Main groups of variables (see `.env.example` for the full list):

- **Database**: `DATABASE_*`.
- **Email** (password reset): `EMAIL_HOST`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD` (a Gmail **App Password**, never the account password)
  and `DEFAULT_FROM_EMAIL`.
- **Security**: `SESSION_COOKIE_AGE`, `SESSION_EXPIRE_AT_BROWSER_CLOSE`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`,
  `AXES_ENABLED`, `AXES_FAILURE_LIMIT`, `AXES_COOLOFF_MINUTES`.

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
- PostgreSQL: not published to the host (only `web` reaches it on the compose network); use `docker compose exec db psql -U taskforge` if you need a shell.

`db` is bound to `127.0.0.1`; `web` is published on the LAN (so office clients
can use it without a VPN). `web` runs `runserver --insecure` so static files are
served with `DEBUG=0`. Remote users go through Tailscale (see below).

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

Follow the prompts, then sign in at http://localhost:8000/admin. The user is
created with `role=MEMBER`; set **Role = Admin** there to get admin powers.

## Accounts & password reset

- Self-registration at `/accounts/register/` creates an **inactive** user.
  Approve it from `/admin` with the action **"Approve selected users
  (activate)"** before the person can log in.
- Password reset lives at `/accounts/password_reset/` and sends the reset link
  by email (Gmail SMTP by default, see the `EMAIL_*` variables). Without email
  credentials configured, reset emails are not delivered.
- Brute-force protection (`django-axes`) locks a username+IP after 5 failed
  logins for 30 minutes; unlock from `/admin` or with the `axes_reset` command.

## Start the project

```bash
docker compose up
```

## Deploy on a server

The whole stack is plain Docker Compose, so it runs on any machine with Docker
(a Linux server, mini PC, NAS or VPS) — nothing is tied to the development
laptop. The server needs **Docker Engine + Compose v2** (on Linux you do not
need Docker Desktop).

1. Get the code on the server (private repo: invite the person as a
   collaborator first):

   ```bash
   git clone https://github.com/YovanyPerez/TaskForge.git
   cd TaskForge
   ```

   Or download the ZIP from GitHub (`Code → Download ZIP`) and extract it.

2. Create the environment file and fill in real values:

   ```bash
   cp .env.example .env
   ```

   - `SECRET_KEY`: generate a new one, e.g.
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
   - `DATABASE_*`: keep the defaults or change them before the first boot.
   - `EMAIL_*` + `DEFAULT_FROM_EMAIL`: only needed for password reset.
   - `DJANGO_ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`: the server's IP/host and,
     for remote access, its `*.ts.net` name.

   **Never copy another installation's `.env`** — it contains secrets.

3. Start it (migrations run automatically):

   ```bash
   docker compose up -d
   ```

   The app is then at `http://<server-ip>:8000`. For access from outside the
   office, install Tailscale on the server (see
   [Access from outside](#access-from-outside-tailscale)).

### Moving existing data

To bring projects/users from an old installation, stop the app on the new
machine and dump/restore the database:

```bash
# old machine
docker compose exec -T db sh -c \
  'pg_dump --clean --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB"' > taskforge.sql

# new machine
docker compose up -d
docker compose stop web
docker compose exec -T db sh -c \
  'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < taskforge.sql
docker compose start web
```

(`$POSTGRES_USER` / `$POSTGRES_DB` are expanded inside the `db` container.)

### Server notes

- `web` runs Django's development server (`runserver --insecure`). That is fine
  for a small internal team; for heavier or public use, switch to `gunicorn`
  plus a static-file server (whitenoise/nginx).
- Schedule regular `pg_dump` backups (cron): the database lives in the
  `postgres_data` Docker volume, so losing the disk without a backup loses all
  data.

## Desktop client (Windows)

`desktop/` contains a Tauri v2 wrapper that shows the app in a native window
(WebView2). It is optional: the web UI keeps working as usual.

- Build: see `desktop/README.md` (needs Node, Rust and VS Build Tools).
- The client tries a list of server URLs and uses the first one that responds
  (Tailscale name first, then the LAN host/IP), so the same installer works
  inside the office and from outside. Override with a `taskforge.json` file
  next to the `.exe` (`server_urls`).
- If no server responds, it shows an offline screen with a **Retry** button.

### Access from outside (Tailscale)

1. Install Tailscale on the server and run `tailscale up`.
2. In the Tailscale admin console, enable **MagicDNS** and **HTTPS
   certificates**, note the machine name (`<machine>.<tailnet>.ts.net`).
3. Expose the Django port over HTTPS:

   ```bash
   tailscale serve --bg --https=443 http://127.0.0.1:8000
   ```

4. In `.env` set `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to include
   the `*.ts.net` name, then `docker compose up -d`.

Remote users install Tailscale once (same account) and then just open the
TaskForge program. Office users do not need Tailscale: the `web` port is
published on the LAN (`http://<server>:8000`).

> Security note: because LAN clients use plain HTTP, `SESSION_COOKIE_SECURE`
> and `CSRF_COOKIE_SECURE` stay `0` (otherwise LAN logins would not persist).
> Traffic over Tailscale is still encrypted by WireGuard.

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
- `/api/users/` is restricted to `ADMIN`/`MANAGER` (avoids email disclosure to
  members).
- Comments can be created by any project member; only the author or an
  `ADMIN`/`MANAGER` can modify or delete a comment.
- `POST /api/token-auth/` is rate-limited (10/min per IP).

## Run tests

```bash
docker compose run --rm web python manage.py test
```
