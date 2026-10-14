import datetime

import pytest
from sqlalchemy import Column, MetaData, String, Table, Text, create_engine, func, insert, select
from sqlalchemy.dialects import sqlite
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from neteye.extensions import db as _db
from neteye.lib.utils import legacy_credentials
from neteye.lib.utils.database_bootstrap import DatabaseNotReadyError, check_credentials_encrypted
from neteye.lib.utils.legacy_credentials import (
    CredentialState,
    classify,
    encrypt_legacy_credentials_command,
    encrypt_plaintext_credentials,
    scan_credentials,
)
from neteye.node.models import Node

NOW = datetime.datetime(2026, 1, 1)
NODE_COLUMNS = ("id", "hostname", "ip_address", "port", "password", "enable",
                "created_at", "updated_at")
VERSION_COLUMNS = ("id", "transaction_id", "operation_type", "password", "enable")


@pytest.fixture
def engine(app, tmp_path):
    """A migrated-shaped database of its own, so plaintext rows never leak into
    the shared test database."""
    engine = create_engine(f"sqlite:///{tmp_path / 'credentials.db'}")
    with app.app_context():
        _db.metadata.create_all(engine)
    yield engine
    engine.dispose()


def password_type():
    return Node.__table__.c.password.type


def encrypt(engine, value):
    return password_type().process_bind_param(value, engine.dialect)


def decrypt(engine, value):
    return password_type().process_result_value(value, engine.dialect)


def raw_table(name, columns):
    return Table(name, MetaData(), *(Column(column_name, String) for column_name in columns))


def insert_node(engine, node_id, password, enable=None):
    nodes = raw_table("nodes", NODE_COLUMNS)
    with engine.begin() as connection:
        connection.execute(insert(nodes).values(
            id=node_id, hostname=node_id, ip_address="192.0.2.1", port=22,
            password=password, enable=enable, created_at=NOW, updated_at=NOW,
        ))


def insert_version(engine, node_id, transaction_id, password):
    versions = raw_table("nodes_version", VERSION_COLUMNS)
    with engine.begin() as connection:
        connection.execute(insert(versions).values(
            id=node_id, transaction_id=transaction_id, operation_type=0, password=password,
        ))


def raw_values(engine, table_name):
    table = raw_table(table_name, ("id", "password", "enable"))
    with engine.connect() as connection:
        return {row.id: (row.password, row.enable) for row in connection.execute(select(table))}


def version_count(engine):
    with engine.connect() as connection:
        return connection.execute(
            select(func.count()).select_from(raw_table("nodes_version", ("id",)))
        ).scalar()


def foreign_ciphertext():
    """A credential encrypted with some other NODE_CREDENTIAL_KEY."""
    other_key_type = StringEncryptedType(Text, "some-other-key", AesEngine, "pkcs5")
    return other_key_type.process_bind_param("cisco-from-another-install", sqlite.dialect())


class TestClassify:
    def test_value_encrypted_with_current_key(self, engine):
        assert classify(encrypt(engine, "cisco"), password_type(), engine.dialect) is CredentialState.ENCRYPTED

    @pytest.mark.parametrize("value", ["cisco", "Cisco123", "", "p@ss word!"])
    def test_plaintext(self, engine, value):
        assert classify(value, password_type(), engine.dialect) is CredentialState.PLAINTEXT

    def test_ciphertext_from_another_key_is_undecryptable(self, engine):
        assert classify(foreign_ciphertext(), password_type(), engine.dialect) is CredentialState.UNDECRYPTABLE


class TestEncryptPlaintextCredentials:
    def test_plaintext_in_nodes_and_history_is_encrypted(self, engine):
        already_encrypted = encrypt(engine, "keep-me")
        insert_node(engine, "legacy", password="cisco", enable="enable-secret")
        insert_node(engine, "modern", password=already_encrypted)
        insert_version(engine, "legacy", 1, "old-cisco")
        versions_before = version_count(engine)

        written = encrypt_plaintext_credentials(engine, scan_credentials(engine))

        assert written == 3
        nodes = raw_values(engine, "nodes")
        assert decrypt(engine, nodes["legacy"][0]) == "cisco"
        assert decrypt(engine, nodes["legacy"][1]) == "enable-secret"
        assert nodes["modern"][0] == already_encrypted
        assert decrypt(engine, raw_values(engine, "nodes_version")["legacy"][0]) == "old-cisco"
        # Core updates bypass Continuum: the rewrite is not a new version.
        assert version_count(engine) == versions_before
        assert {value.state for value in scan_credentials(engine)} == {CredentialState.ENCRYPTED}

    def test_running_twice_changes_nothing(self, engine):
        insert_node(engine, "legacy", password="cisco")
        encrypt_plaintext_credentials(engine, scan_credentials(engine))
        after_first_run = raw_values(engine, "nodes")

        assert encrypt_plaintext_credentials(engine, scan_credentials(engine)) == 0
        assert raw_values(engine, "nodes") == after_first_run

    def test_undecryptable_value_blocks_all_writes(self, engine):
        insert_node(engine, "legacy", password="cisco")
        insert_node(engine, "wrong-key", password=foreign_ciphertext())
        before = raw_values(engine, "nodes")

        with pytest.raises(Exception, match="NODE_CREDENTIAL_KEY"):
            encrypt_plaintext_credentials(engine, scan_credentials(engine))
        assert raw_values(engine, "nodes") == before


class TestCommand:
    @pytest.fixture
    def run(self, app, engine, monkeypatch):
        monkeypatch.setattr(legacy_credentials, "db", type("FakeDb", (), {"engine": engine}))

        def run(*args):
            with app.app_context():
                return app.test_cli_runner().invoke(encrypt_legacy_credentials_command, list(args))
        return run

    def test_dry_run_reports_without_writing(self, run, engine):
        insert_node(engine, "legacy", password="cisco")
        result = run()
        assert result.exit_code == 0
        assert "plaintext: 1" in result.output
        assert "Dry run" in result.output
        assert "cisco" not in result.output
        assert raw_values(engine, "nodes")["legacy"][0] == "cisco"

    def test_apply_encrypts(self, run, engine):
        insert_node(engine, "legacy", password="cisco")
        result = run("--apply")
        assert result.exit_code == 0
        assert "Encrypted 1 value(s)." in result.output
        assert decrypt(engine, raw_values(engine, "nodes")["legacy"][0]) == "cisco"

    def test_undecryptable_fails_even_as_dry_run(self, run, engine):
        insert_node(engine, "wrong-key", password=foreign_ciphertext())
        result = run("--apply")
        assert result.exit_code != 0
        assert "NODE_CREDENTIAL_KEY" in result.output


class TestStartupCheck:
    def test_encrypted_database_passes(self, engine):
        insert_node(engine, "modern", password=encrypt(engine, "cisco"))
        check_credentials_encrypted(engine)

    def test_plaintext_refuses_startup_with_command(self, engine):
        insert_node(engine, "legacy", password="cisco")
        with pytest.raises(DatabaseNotReadyError, match="encrypt-legacy-credentials --apply"):
            check_credentials_encrypted(engine)

    def test_undecryptable_refuses_startup(self, engine):
        insert_node(engine, "wrong-key", password=foreign_ciphertext())
        with pytest.raises(DatabaseNotReadyError, match="NODE_CREDENTIAL_KEY"):
            check_credentials_encrypted(engine)
