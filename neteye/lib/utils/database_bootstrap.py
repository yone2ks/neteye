"""Bring the database to a usable state before the app starts serving.

Schema changes are managed by Alembic (Flask-Migrate). On startup:

* empty database      -> create the schema with ``upgrade`` (fresh install)
* schema at head      -> nothing to do
* schema behind head  -> refuse to start; the operator runs ``flask db upgrade``
                         after taking a backup
* tables but no Alembic revision (created by ``db.create_all()`` before
  migrations existed) -> refuse to start; the operator stamps the baseline
  revision, upgrades, and checks ``flask schema-diff``

Only the empty-database case migrates automatically: it has no data to lose.

Node credentials still stored in plaintext (databases from before encryption
at rest) also refuse startup; see ``legacy_credentials``.
"""
import enum
import logging

import click

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask import current_app
from flask_migrate import upgrade
from sqlalchemy import inspect

from neteye.extensions import db
from neteye.lib.utils.legacy_credentials import (ENCRYPT_COMMAND,
                                                 CredentialState,
                                                 scan_credentials)

logger = logging.getLogger(__name__)

ALEMBIC_VERSION_TABLE = "alembic_version"
# Schema produced by db.create_all() just before Flask-Migrate was introduced.
# Databases created before then are stamped with this revision, never head,
# so that later migrations still run on them.
BASELINE_REVISION = "0001"
UPGRADE_COMMAND = "flask --app neteye db upgrade"
SCHEMA_DIFF_COMMAND = "flask --app neteye schema-diff"


class DatabaseState(enum.Enum):
    EMPTY = "empty"
    UNVERSIONED = "unversioned"
    OUTDATED = "outdated"
    CURRENT = "current"


class DatabaseNotReadyError(RuntimeError):
    """The schema needs operator action before the app can start."""


def get_head_revision() -> str:
    config = current_app.extensions["migrate"].migrate.get_config()
    return ScriptDirectory.from_config(config).get_current_head()


def get_database_state(engine, head_revision: str) -> DatabaseState:
    with engine.connect() as connection:
        table_names = set(inspect(connection).get_table_names())
        if not table_names:
            return DatabaseState.EMPTY
        if ALEMBIC_VERSION_TABLE not in table_names:
            return DatabaseState.UNVERSIONED
        current_revision = MigrationContext.configure(connection).get_current_revision()
    if current_revision != head_revision:
        return DatabaseState.OUTDATED
    return DatabaseState.CURRENT


def get_schema_differences(engine, metadata) -> list:
    """Return Alembic's diff between the live database and the models.

    An empty list means the database matches the models.
    """
    with engine.connect() as connection:
        return compare_metadata(MigrationContext.configure(connection), metadata)


def ensure_database_ready() -> None:
    """Create or verify the schema, then seed roles and the admin user.

    Must be called inside an application context.
    """
    # Imported here so this module does not import models at load time.
    from neteye.user.models import initialize_admin, initialize_roles

    head_revision = get_head_revision()
    state = get_database_state(db.engine, head_revision)

    if state is DatabaseState.EMPTY:
        logger.info("Empty database: creating schema at revision %s", head_revision)
        upgrade()
    elif state is DatabaseState.UNVERSIONED:
        raise DatabaseNotReadyError(
            "The database has tables but no migration revision (it was created "
            "before Flask-Migrate was introduced). Back up the database, run "
            f"`flask --app neteye db stamp {BASELINE_REVISION}` and "
            f"`{UPGRADE_COMMAND}`, then check that `{SCHEMA_DIFF_COMMAND}` "
            "reports no differences."
        )
    elif state is DatabaseState.OUTDATED:
        raise DatabaseNotReadyError(
            "The database schema is older than this version of neteye. Back up "
            f"the database, then run `{UPGRADE_COMMAND}`."
        )

    check_credentials_encrypted(db.engine)
    initialize_roles()
    initialize_admin()


def check_credentials_encrypted(engine) -> None:
    states = {value.state for value in scan_credentials(engine)}
    if CredentialState.UNDECRYPTABLE in states:
        raise DatabaseNotReadyError(
            "Some node credentials do not decrypt with the current "
            f"NODE_CREDENTIAL_KEY. Check the key; `{ENCRYPT_COMMAND}` lists "
            "the affected rows."
        )
    if CredentialState.PLAINTEXT in states:
        raise DatabaseNotReadyError(
            "Some node credentials are stored in plaintext (created before "
            f"encryption at rest). Back up the database, review `{ENCRYPT_COMMAND}`, "
            f"then run `{ENCRYPT_COMMAND} --apply`."
        )


@click.command("schema-diff")
def schema_diff_command():
    """Show differences between the database schema and the models."""
    differences = get_schema_differences(db.engine, db.metadata)
    if not differences:
        click.echo("Database schema matches the models.")
        return
    for difference in differences:
        click.echo(repr(difference))
    raise SystemExit(1)
