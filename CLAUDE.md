# Neteye — Claude Code Instructions

## Project Overview

Neteye is a Flask-based web application for managing network devices. It provides a GUI and REST API for registering devices, executing commands via SSH, parsing outputs with ntc-templates, and tracking change history.

## Tech Stack

- **Backend**: Python 3.10+, Flask 3.x, SQLAlchemy 2.x (via Flask-SQLAlchemy)
- **Auth**: Flask-Security-Too 5.x (argon2 password hashing, token auth for API)
- **Config**: Dynaconf (settings.toml + .env + settings.local.toml)
- **History/Versioning**: SQLAlchemy-Continuum
- **SSH**: Netmiko, Scrapli, NAPALM
- **Templates**: Jinja2, CoreUI (Bootstrap admin template)
- **Testing**: pytest

## Directory Structure

```
neteye/                  # Flask application package
  blueprints.py          # bp_factory() — creates all Blueprints
  extensions.py          # Flask extension instances (db, security, settings, ...)
  <resource>/            # One directory per resource (node, interface, cable, ...)
    models.py            # SQLAlchemy model
    routes.py            # Blueprint routes
    schemas.py           # Marshmallow schema (REST API serialization)
    forms.py             # WTForms form
  api/                   # Flask-RESTX API namespace definitions
  history/               # @record_history decorator and history models
  lib/utils/             # Shared utilities (report_exception, log filters, ...)
  security/              # Flask-Security-Too setup and user/role models
manage.py                # Entry point: python manage.py
settings.toml            # Default config (do NOT edit directly)
.env                     # Secrets — git-ignored, never commit
settings.local.toml      # Local overrides — git-ignored, never commit
```

## Common Commands

```shell
# Run application
python manage.py

# Run tests
ENV_FOR_DYNACONF=testing python -m pytest

# Run tests with coverage
ENV_FOR_DYNACONF=testing python -m pytest --cov=neteye --cov-report=term-missing
```

## Configuration (3-file pattern)

| File | Purpose | Git-tracked |
|------|---------|-------------|
| `.env` | Secrets (SECRET_KEY, ADMIN_PASSWORD, credentials) | No — never commit |
| `settings.toml` | Application defaults | Yes — do not edit directly |
| `settings.local.toml` | Local overrides (DB path, timeouts, etc.) | No — never commit |

- Access config in code: `from neteye.extensions import settings`
- Environment variables with `NETEYE_` prefix override any setting (e.g. `NETEYE_PORT=8080`)
- Copy `.env.example` → `.env` and fill in values before first run

## Testing

- Test environment uses `[testing]` section in `settings.toml` (SQLite at `/tmp/neteye_test.db`, CSRF disabled)
- Always prefix test runs with `ENV_FOR_DYNACONF=testing`
- `conftest.py` provides `flask_app` and `client` fixtures — do not recreate them in tests

## Architecture Patterns

**Blueprint factory** — never instantiate Blueprint directly:
```python
from neteye.blueprints import bp_factory
bp = bp_factory("myresource")  # neteye/blueprints.py
```

**History recording** — use decorator, not manual calls:
```python
from neteye.history import record_history
@record_history
def update_node(...): ...
```

**Exception handling** — use shared utility:
```python
from neteye.lib.utils.report_exception import report_exception
except Exception as e:
    report_exception(e)
```

## Code Quality Standards

- No `print()` statements — use `logging` module instead
- No raw SQL — use SQLAlchemy ORM or Core expressions
- No secrets in code — use `.env` or `settings.local.toml`
- Type hints are recommended but not required

### Naming Conventions

**Python**
- `snake_case` for functions and variables
- `PascalCase` for classes
- `SCREAMING_SNAKE_CASE` for module-level constants

**JavaScript**
- `camelCase` for variables and functions
- `SCREAMING_SNAKE_CASE` for module-level constants (e.g. `STORAGE_PREFIX`, not `SK`)
- No cryptic abbreviations or single-letter names except loop counters (`i`, `j`) — use descriptive names that make the intent clear without needing a comment

**localStorage keys**
- Prefix with `neteye_<feature>_` to avoid collisions with other libraries (e.g. DataTables uses unprefixed keys)
- Example: `neteye_ping_node_id`, `neteye_ping_src_ip`

## Git Workflow

- Run `git checkout -b <branch>` **before** creating any files or directories
- Never commit directly to master
- Branch naming: `fix/`, `feature/`, `refactor/`, `docs/`
- Create a PR and merge into master when done

## Commit Messages

- Do NOT include `Co-Authored-By` lines
- Before committing: show a summary of changes and `git diff`, then wait for user confirmation

## Proposing Recommendations

When proposing options, evaluate from 3 perspectives and state the recommended option:

1. **Network Engineer perspective**: operational and design considerations
2. **Software Engineer perspective**: code quality, maintainability, security
3. **Critical perspective**: trade-offs, risks, blind spots of the above two

→ **Recommendation**: `<option>` — `<one or two sentence rationale>`
