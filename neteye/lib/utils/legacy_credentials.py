"""Encrypt node credentials stored before encryption at rest was introduced.

Databases created before #52 hold ``nodes.password`` / ``nodes.enable`` (and
their SQLAlchemy-Continuum history in ``nodes_version``) in plaintext. The
column type now decrypts on load, so such rows raise on every query.

Each stored value is classified:

* ``ENCRYPTED``      -- decrypts with the current NODE_CREDENTIAL_KEY
* ``PLAINTEXT``      -- does not decrypt and is not shaped like ciphertext
* ``UNDECRYPTABLE``  -- shaped like ciphertext but does not decrypt, which
                        usually means NODE_CREDENTIAL_KEY is wrong

Encrypting while any value is UNDECRYPTABLE is refused: with a wrong key,
re-encrypting would make the credentials unrecoverable.

Rows are updated with Core statements, so Continuum does not record the
rewrite as a new version. Values are never logged or printed.
"""
import base64
import binascii
import enum
from dataclasses import dataclass

import click
from sqlalchemy import column, select, table, update

from neteye.extensions import db

ENCRYPT_COMMAND = "flask --app neteye encrypt-legacy-credentials"
CREDENTIAL_COLUMNS = ("password", "enable")
# Table name -> primary key columns. nodes_version is Continuum's history table.
CREDENTIAL_TABLES = {
    "nodes": ("id",),
    "nodes_version": ("id", "transaction_id"),
}
AES_BLOCK_SIZE = 16


class CredentialState(enum.Enum):
    ENCRYPTED = "encrypted"
    PLAINTEXT = "plaintext"
    UNDECRYPTABLE = "undecryptable"


@dataclass(frozen=True)
class CredentialValue:
    table_name: str
    column_name: str
    primary_key: tuple
    state: CredentialState
    # Kept only to encrypt PLAINTEXT values; never shown.
    raw_value: str


def _credential_type(column_name):
    # Imported here so this module does not import models at load time.
    from neteye.node.models import Node

    return Node.__table__.c[column_name].type


def _looks_like_ciphertext(value: str) -> bool:
    """AesEngine stores base64 of a whole number of AES blocks."""
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return False
    return len(decoded) > 0 and len(decoded) % AES_BLOCK_SIZE == 0


def classify(value: str, column_type, dialect) -> CredentialState:
    try:
        column_type.process_result_value(value, dialect)
        return CredentialState.ENCRYPTED
    except Exception:
        pass
    if _looks_like_ciphertext(value):
        return CredentialState.UNDECRYPTABLE
    return CredentialState.PLAINTEXT


def _raw_table(table_name):
    """Untyped view of a table so values are read without decryption."""
    columns = CREDENTIAL_TABLES[table_name] + CREDENTIAL_COLUMNS
    return table(table_name, *(column(name) for name in columns))


def scan_credentials(engine) -> list:
    """Classify every non-NULL credential value in nodes and nodes_version."""
    dialect = engine.dialect
    values = []
    with engine.connect() as connection:
        for table_name, key_columns in CREDENTIAL_TABLES.items():
            raw_table = _raw_table(table_name)
            for row in connection.execute(select(raw_table)).mappings():
                primary_key = tuple(row[name] for name in key_columns)
                for column_name in CREDENTIAL_COLUMNS:
                    raw_value = row[column_name]
                    if raw_value is None:
                        continue
                    state = classify(raw_value, _credential_type(column_name), dialect)
                    values.append(
                        CredentialValue(table_name, column_name, primary_key, state, raw_value)
                    )
    return values


def encrypt_plaintext_credentials(engine, values) -> int:
    """Encrypt PLAINTEXT values in one transaction; return how many were written."""
    if any(value.state is CredentialState.UNDECRYPTABLE for value in values):
        raise click.ClickException(
            "Some credentials look encrypted but do not decrypt with the current "
            "NODE_CREDENTIAL_KEY. Nothing was changed."
        )
    plaintext_values = [value for value in values if value.state is CredentialState.PLAINTEXT]
    dialect = engine.dialect
    with engine.begin() as connection:
        for value in plaintext_values:
            raw_table = _raw_table(value.table_name)
            key_columns = CREDENTIAL_TABLES[value.table_name]
            encrypted = _credential_type(value.column_name).process_bind_param(
                value.raw_value, dialect
            )
            statement = update(raw_table).values({value.column_name: encrypted})
            for name, key in zip(key_columns, value.primary_key):
                statement = statement.where(raw_table.c[name] == key)
            connection.execute(statement)
    return len(plaintext_values)


def _echo_report(values):
    for state in CredentialState:
        matching = [value for value in values if value.state is state]
        click.echo(f"{state.value}: {len(matching)}")
        if state is CredentialState.ENCRYPTED:
            continue
        for value in matching:
            click.echo(f"  {value.table_name}.{value.column_name} key={value.primary_key}")


@click.command("encrypt-legacy-credentials")
@click.option("--apply", "apply_changes", is_flag=True,
              help="Write the changes. Without it, only report what would change.")
def encrypt_legacy_credentials_command(apply_changes):
    """Encrypt node passwords/enable secrets still stored in plaintext."""
    values = scan_credentials(db.engine)
    _echo_report(values)
    if any(value.state is CredentialState.UNDECRYPTABLE for value in values):
        raise click.ClickException(
            "Undecryptable values found: check NODE_CREDENTIAL_KEY. Nothing was changed."
        )
    if not apply_changes:
        click.echo("Dry run: nothing was changed. Back up the database and re-run with --apply.")
        return
    written = encrypt_plaintext_credentials(db.engine, values)
    click.echo(f"Encrypted {written} value(s).")
