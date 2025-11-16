<!-- Copilot / AI agent instructions for the RUC_baplatform repo -->
# Quick Start for AI coding agents

This file captures the minimal, actionable knowledge an AI agent needs to be productive in this repository.

- **Project type:** Django web application (legacy: Django 2.2, Python 3.7)
- **Project root:** the runnable Django project lives in the `baplatform/` folder.

**Where to look (high-value files)**
- `baplatform/manage.py` — entrypoint for running tasks (migrate, runserver, tests).
- `baplatform/baplatform/settings.py` — central configuration (DB, static/media, INSTALLED_APPS).
- `baplatform/baplatform/urls.py` — URL routing; most views are under `baweb.views.*` modules.
- `baweb/` — main app: `views/`, `forms/`, `models.py`, `templates/`, `static/`, `migrations/`.
- `db.sqlite3` — default database (SQLite) at project root; migrations exist under `baweb/migrations/`.
- `baplatform/readme.txt` — quick, project-specific notes (Python 3.7, how to inspect sqlite3)
- `requirements.txt` — dependency list (Django 2.2.12, django-ckeditor, Werkzeug integration).

**Big-picture architecture and data flow**
- Single Django project with one primary app: `baweb`. The app implements user, teacher, student, course, assignment, file and announcement features.
- Routing: `baplatform/baplatform/urls.py` maps many endpoints to functions in `baweb.views` modules (e.g. `user`, `admin`, `course`, `assignment`). Use this file to discover surface endpoints and which view module to edit for a route.
- Persistence: default SQLite DB `db.sqlite3`. Models live in `baweb/models.py` and are versioned via `baweb/migrations/`.
- Media & uploads: configured in `baplatform/baplatform/settings.py`: `MEDIA_ROOT = <project>/media`, `CKEDITOR_UPLOAD_PATH` used for rich-text uploads.
- Static files: `baweb/static/` and `STATICFILES_DIRS` configured; `STATIC_ROOT` set to `static/ckeditor` in settings.
- Middleware and auth: `baweb.middleware.auto.AuthMiddleware` is injected; check `baweb/middleware/auto.py` for auth/session behaviors.

**Developer workflows (commands & environment)**
- Activate virtual environment (project includes `baplatform_env/`): in PowerShell
  ```powershell
  .\baplatform_env\Scripts\Activate.ps1
  ```
- Install deps (if venv not present):
  ```powershell
  pip install -r baplatform/requirements.txt
  ```
- Apply migrations and run dev server (Django 2.2):
  ```powershell
  cd baplatform
  python manage.py migrate
  python manage.py runserver 0.0.0.0:8000
  ```
- Run tests (if any):
  ```powershell
  cd baplatform
  python manage.py test
  ```
- Inspect DB (sqlite3):
  ```powershell
  sqlite3 db.sqlite3
  .tables
  .schema baweb_<modelname>
  ```

**Project-specific conventions & patterns**
- Views are organized by feature modules under `baweb.views` (e.g. `baweb/views/user.py`, `baweb/views/course.py`). When adding or modifying endpoints, update the corresponding module and `baplatform/urls.py` if adding a new route.
- Forms are under `baweb/forms/` grouped by function (`assignmentforms.py`, `courseforms.py`, etc.). Prefer these form classes for input validation rather than ad-hoc request parsing.
- Templates: `baweb/templates/` follow conventional Django template names; layout is in `layout.html` and reused by pages like `course_page.html` and `assignment_page.html`.
- File uploads use `MEDIA_ROOT` and CKEditor upload settings — prefer using the `ckeditor` upload endpoints already included in `urls.py` (`path('ckeditor/', include('ckeditor_uploader.urls'))`).
- Security: `settings.py` currently has `DEBUG=True` and a hard-coded `SECRET_KEY`. Avoid committing changes that leak production secrets; treat this repo as development-only unless instructed otherwise.

**Integration points & external dependencies**
- `django-ckeditor` for rich-text editing and file uploads — check `CKEDITOR_CONFIGS` in `settings.py` and `baweb/static/ckeditor` for custom static assets.
- `werkzeug_debugger_runserver` is included in `INSTALLED_APPS` — repository may use the Werkzeug debugger for development. Use with caution; follow package docs.
- `sslserver` is included — repo can be extended to serve HTTPS in dev.

**Common tasks for an AI agent (concise recipes)**
- Find the view for a route: open `baplatform/urls.py`, locate the `path(...)` and note the module imported from `baweb.views`. Edit that module.
- Add a new model migration:
  1. Edit `baweb/models.py` (or add a new models file and import it from `baweb.__init__` if needed).
  2. Run `python manage.py makemigrations baweb` then `python manage.py migrate`.
- Fix an HTML/template issue: templates live in `baweb/templates/`. Use the base `layout.html` as the entry point.

**Examples from this codebase**
- Route → view mapping: `path('home/load/', home.home_load)` maps to function `home_load` in `baweb/views/home.py`.
- Middleware: `baweb.middleware.auto.AuthMiddleware` is in `MIDDLEWARE` — check it when debugging authentication/session issues.
- Static/media paths: `MEDIA_ROOT` → `<repo>/media`; `CKEDITOR_UPLOAD_PATH` → `<repo>/media/uploads`.

If anything in this file looks incomplete or you want more detail (e.g., common PR patterns, branch names, or a VS Code `launch.json`), tell me which area and I'll expand the instructions.
