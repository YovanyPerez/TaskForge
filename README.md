# TaskForge

Plataforma de gestión de proyectos y tareas — un sistema ligero y autoalojado
inspirado en versiones simplificadas de Jira y Trello.

## Características

- **Usuarios y roles**: `ADMIN`, `MANAGER`, `MEMBER` con la autenticación
  integrada de Django. El registro crea una cuenta **inactiva** hasta que un
  administrador la aprueba.
- **Proyectos**: crear, seguir su estado (`Planning`, `In Progress`, `Completed`, `On Hold`) y gestionar miembros.
- **Tareas**: crear, asignar, priorizar y seguir su estado (`To Do`, `In Progress`, `Done`).
- **Comentarios**: discutir tareas.
- **Panel y reportes**: resumen de proyectos, tareas, carga de trabajo y vencidas.
- **Tablero global de tareas** y **directorio del equipo**.
- **Notificaciones**: campana con contador de no leídas — avisa cuando te asignan
  una tarea, te agregan a un proyecto o se completa una tarea/proyecto.
- **Recuperación de contraseña**: enlace de restablecimiento por correo (Gmail
  SMTP), sin revelar si una cuenta existe.
- **Seguridad**: control de acceso por roles, bloqueo por fuerza bruta con
  `django-axes`, límite de peticiones en la API, registro sujeto a aprobación y
  sesiones/cookies configurables por entorno.
- **Cliente de escritorio**: app opcional para Windows (Tauri/WebView2) que
  funciona en la LAN y desde fuera con Tailscale.
- **API REST**: API JSON para todos los recursos.
- **Ajustes**: idioma de la interfaz (English/Español) guardado por usuario, más
  opciones de apariencia locales del navegador (color de acento, densidad).

> Estado: funcionalmente completo para uso interno — auth (+ recuperación de
> contraseña), proyectos, tareas, comentarios, panel, reportes, API REST,
> permisos y seguridad, notificaciones, i18n y el cliente de escritorio están
> listos. Queda pulido de UI/UX.

## Cómo usar TaskForge

Hay tres formas de usarlo. Todas necesitan el **servidor** (el PC que corre
Docker) encendido y con el stack levantado; el programa de escritorio y el
acceso remoto también necesitan **Tailscale** conectado.

1. **Oficina — cualquier navegador (sin instalar nada):**
   abre `http://<server-host>:8000` (o `http://<server-ip>:8000`) e inicia sesión.
2. **Desde casa — cualquier navegador (Tailscale):**
   conecta Tailscale, abre `https://<machine>.<tailnet>.ts.net` e inicia sesión.
3. **Programa de escritorio (.exe):**
   instala `TaskForge_0.1.0_x64-setup.exe` una vez (ver
   [desktop/README.md](desktop/README.md)), y luego abre **TaskForge** desde el
   menú Inicio. El mismo programa sirve en la oficina y desde casa: prueba
   primero el nombre de Tailscale y después la LAN, y usa el primero que
   responda. Si ninguno responde, muestra una pantalla con **Reintentar** que
   pide revisar la red/VPN.

Las URLs reales del despliegue no se suben al repo: viven en tu `.env`
(servidor) y se incrustan en el cliente al compilarlo (ver `desktop/README.md`).

Las cuentas nuevas deben ser aprobadas por un administrador antes del primer
inicio de sesión (ver
[Cuentas y recuperación de contraseña](#cuentas-y-recuperación-de-contraseña)).

## Stack tecnológico

- **Backend**: Python 3.12, Django 5.2 LTS, Django REST Framework
- **Base de datos**: PostgreSQL 16
- **Frontend**: Django Templates, Bootstrap 5 (CDN), JavaScript vanilla
- **Seguridad**: `django-axes` (bloqueo por fuerza bruta), throttling de DRF
- **Cliente de escritorio**: Tauri v2 (Rust) + WebView2, opcional y solo Windows
- **Acceso remoto**: Tailscale (`tailscale serve`, HTTPS)
- **Desarrollo**: Docker, Docker Compose, Git
- **Pruebas**: runner integrado de Django (+ `cargo test` para el cliente)

## Arquitectura

El proyecto se divide en `backend/` (proyecto Django), `frontend/` (plantillas
+ estáticos) y un `desktop/` opcional (cliente Tauri). El frontend se renderiza
en el servidor y se mantiene separado del backend para poder evolucionar de
forma independiente.

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

Cada app de dominio es dueña de sus modelos, su registro en el admin y sus
propias pruebas.

## Estructura de carpetas

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

## Requisitos

- Docker (con Docker Compose v2)

Para correr el servidor no hace falta nada más localmente — todo va en
contenedores. Compilar el cliente de escritorio opcional requiere además Node,
Rust y VS Build Tools (ver `desktop/README.md`).

## Configuración del entorno

1. Copia el archivo de entorno de ejemplo:

   ```bash
   cp .env.example .env
   ```

2. Edita `.env` y pon un `SECRET_KEY` real (cualquier cadena larga aleatoria
   sirve para desarrollo). Los valores de base de datos los usa Docker Compose
   y ya vienen configurados para desarrollo local.

Grupos principales de variables (la lista completa está en `.env.example`):

- **Base de datos**: `DATABASE_*`.
- **Correo** (recuperación de contraseña): `EMAIL_HOST`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD` (una **App Password** de Gmail, nunca la contraseña de
  la cuenta) y `DEFAULT_FROM_EMAIL`.
- **Seguridad**: `SESSION_COOKIE_AGE`, `SESSION_EXPIRE_AT_BROWSER_CLOSE`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`,
  `AXES_ENABLED`, `AXES_FAILURE_LIMIT`, `AXES_COOLOFF_MINUTES`.

`.env` está ignorado por git y nunca debe commitearse.

## Docker

Construir y levantar todo el stack:

```bash
docker compose up
```

Esto inicia la aplicación Django y la base de datos PostgreSQL. En la primera
ejecución el Dockerfile construye la imagen (puede tardar unos minutos).

- Django: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- PostgreSQL: no se publica al host (solo `web` lo alcanza en la red de compose); usa `docker compose exec db psql -U taskforge` si necesitas una shell.

`db` escucha en `127.0.0.1`; `web` sí se publica en la LAN (así los clientes de
la oficina lo usan sin VPN). `web` corre `runserver --insecure` para servir los
estáticos con `DEBUG=0`. Los usuarios remotos pasan por Tailscale (ver abajo).

Detén el stack con `Ctrl+C`, o `docker compose down` para eliminar los
contenedores. La base de datos persiste en el volumen `postgres_data`; usa
`docker compose down -v` para borrarla.

## Base de datos

PostgreSQL se aprovisiona automáticamente desde Docker Compose con los valores
de `.env`. No hace falta configuración manual.

## Comandos de migración

Las migraciones corren solas al arrancar el contenedor `web`. Para ejecutarlas
manualmente:

```bash
docker compose run --rm web python manage.py makemigrations
docker compose run --rm web python manage.py migrate
```

## Crear un superusuario

```bash
docker compose run --rm web python manage.py createsuperuser
```

Sigue las indicaciones e inicia sesión en http://localhost:8000/admin. El
usuario se crea con `role=MEMBER`; pon **Role = Admin** ahí para tener permisos
de administración.

## Cuentas y recuperación de contraseña

- El autorregistro en `/accounts/register/` crea un usuario **inactivo**.
  Apruébalo desde `/admin` con la acción **"Approve selected users
  (activate)"** antes de que la persona pueda iniciar sesión.
- La recuperación de contraseña está en `/accounts/password_reset/` y envía el
  enlace por correo (Gmail SMTP por defecto, ver las variables `EMAIL_*`). Sin
  credenciales de correo configuradas, los correos de restablecimiento no se
  envían.
- La protección contra fuerza bruta (`django-axes`) bloquea un usuario+IP tras
  5 intentos fallidos durante 30 minutos; desbloquea desde `/admin` o con el
  comando `axes_reset`.

## Iniciar el proyecto

```bash
docker compose up
```

## Desplegar en un servidor

Todo el stack es Docker Compose puro, así que corre en cualquier máquina con
Docker (un servidor Linux, mini PC, NAS o VPS) — nada está atado a la laptop de
desarrollo. El servidor necesita **Docker Engine + Compose v2** (en Linux no
hace falta Docker Desktop).

1. Consigue el código en el servidor (repo privado: invita primero a la persona
   como colaboradora):

   ```bash
   git clone https://github.com/YovanyPerez/TaskForge.git
   cd TaskForge
   ```

   O descarga el ZIP desde GitHub (`Code → Download ZIP`) y descomprímelo.

2. Crea el archivo de entorno y rellena valores reales:

   ```bash
   cp .env.example .env
   ```

   - `SECRET_KEY`: genera uno nuevo, por ejemplo
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
   - `DATABASE_*`: deja los valores por defecto o cámbialos antes del primer arranque.
   - `EMAIL_*` + `DEFAULT_FROM_EMAIL`: solo hacen falta para la recuperación de contraseña.
   - `DJANGO_ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`: la IP/host del servidor y,
     para acceso remoto, su nombre `*.ts.net`.

   **Nunca copies el `.env` de otra instalación** — contiene secretos.

3. Arráncalo (las migraciones corren solas):

   ```bash
   docker compose up -d
   ```

   La app queda en `http://<server-ip>:8000`. Para acceso desde fuera de la
   oficina, instala Tailscale en el servidor (ver
   [Acceso desde fuera](#acceso-desde-fuera-tailscale)).

### Migrar datos existentes

Para traer proyectos/usuarios de una instalación antigua, para la app en la
máquina nueva y haz dump/restore de la base de datos:

```bash
# máquina antigua
docker compose exec -T db sh -c \
  'pg_dump --clean --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB"' > taskforge.sql

# máquina nueva
docker compose up -d
docker compose stop web
docker compose exec -T db sh -c \
  'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < taskforge.sql
docker compose start web
```

(`$POSTGRES_USER` / `$POSTGRES_DB` se expanden dentro del contenedor `db`.)

### Notas del servidor

- `web` corre el servidor de desarrollo de Django (`runserver --insecure`).
  Está bien para un equipo interno pequeño; para más carga o uso público, cambia
  a `gunicorn` más un servidor de estáticos (whitenoise/nginx).
- Programa backups periódicos con `pg_dump` (cron): la base de datos vive en el
  volumen `postgres_data`, así que perder el disco sin backup es perder todo.

## Cliente de escritorio (Windows)

`desktop/` contiene un envoltorio Tauri v2 que muestra la app en una ventana
nativa (WebView2). Es opcional: la interfaz web sigue funcionando igual.

- Compilar: ver `desktop/README.md` (necesita Node, Rust y VS Build Tools).
- El cliente prueba una lista de URLs del servidor y usa la primera que
  responda (primero el nombre de Tailscale, luego el host/IP de la LAN), así el
  mismo instalador sirve dentro y fuera de la oficina. Se puede sobrescribir con
  un archivo `taskforge.json` junto al `.exe` (`server_urls`).
- Si ningún servidor responde, muestra una pantalla sin conexión con un botón
  **Reintentar**.

### Acceso desde fuera (Tailscale)

1. Instala Tailscale en el servidor y ejecuta `tailscale up`.
2. En la consola de administración de Tailscale, activa **MagicDNS** y
   **certificados HTTPS**, y anota el nombre de la máquina
   (`<machine>.<tailnet>.ts.net`).
3. Expón el puerto de Django por HTTPS:

   ```bash
   tailscale serve --bg --https=443 http://127.0.0.1:8000
   ```

4. En `.env` pon `DJANGO_ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con el nombre
   `*.ts.net`, y luego `docker compose up -d`.

Los usuarios remotos instalan Tailscale una vez (misma cuenta) y después solo
abren el programa TaskForge. Los usuarios de la oficina no necesitan Tailscale:
el puerto de `web` se publica en la LAN (`http://<server>:8000`).

> Nota de seguridad: como los clientes de la LAN usan HTTP plano,
> `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` quedan en `0` (si no, los
> inicios de sesión de la LAN no persistirían). El tráfico por Tailscale sigue
> cifrado por WireGuard.

## API REST

La API se sirve bajo `/api/` (Django REST Framework) y requiere autenticación
(`SessionAuthentication`, la misma sesión que la app web). Con sesión iniciada
hay una API navegable.

| Endpoint | Métodos |
| --- | --- |
| `/api/users/` | `GET`, `GET /api/users/<id>/` (solo lectura) |
| `/api/projects/` | `GET`, `POST` |
| `/api/projects/<id>/` | `GET`, `PUT`, `PATCH`, `DELETE` |
| `/api/tasks/` | `GET`, `POST` |
| `/api/tasks/<id>/` | `GET`, `PUT`, `PATCH`, `DELETE` |
| `/api/comments/` | `GET`, `POST` |
| `/api/comments/<id>/` | `GET`, `PUT`, `PATCH`, `DELETE` |

### Autenticación

- **Sesión**: la misma que la app web (API navegable).
- **Token**: obtén un token con `POST /api/token-auth/` (usuario + contraseña),
  y luego envíalo como `Authorization: Token <key>`.

### Permisos

- `MEMBER` solo ve proyectos/tareas/comentarios donde es miembro.
- `ADMIN`/`MANAGER` ven todo y son los únicos roles que pueden crear,
  actualizar o borrar proyectos y tareas vía API.
- `/api/users/` está restringido a `ADMIN`/`MANAGER` (evita exponer correos a
  los miembros).
- Los comentarios los puede crear cualquier miembro del proyecto; solo el autor
  o un `ADMIN`/`MANAGER` pueden modificarlo o borrarlo.
- `POST /api/token-auth/` tiene límite de peticiones (10/min por IP).

## Ejecutar tests

```bash
docker compose run --rm web python manage.py test
```
