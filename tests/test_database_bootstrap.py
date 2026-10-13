import pytest
from alembic.script import ScriptDirectory
from flask import current_app
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, insert

from neteye.extensions import db as _db
from neteye.lib.utils import database_bootstrap
from neteye.lib.utils.database_bootstrap import (
    BASELINE_REVISION,
    DatabaseNotReadyError,
    DatabaseState,
    ensure_database_ready,
    get_database_state,
    get_head_revision,
    get_schema_differences,
)


@pytest.fixture
def head_revision(app):
    with app.app_context():
        return get_head_revision()


@pytest.fixture
def sqlite_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'state.db'}")
    yield engine
    engine.dispose()


def create_table(engine, name):
    table = Table(name, MetaData(), Column("id", Integer, primary_key=True))
    table.create(engine)


def stamp(engine, revision):
    version_table = Table(
        "alembic_version", MetaData(), Column("version_num", String(32), primary_key=True)
    )
    version_table.create(engine)
    with engine.begin() as connection:
        connection.execute(insert(version_table).values(version_num=revision))


class TestSchemaMatchesMigrations:
    def test_migrated_database_matches_models(self, app):
        """Fails when a model changes without a matching migration."""
        with app.app_context():
            assert get_schema_differences(_db.engine, _db.metadata) == []

    def test_baseline_revision_exists(self, app):
        with app.app_context():
            config = current_app.extensions["migrate"].migrate.get_config()
            script = ScriptDirectory.from_config(config)
            assert script.get_revision(BASELINE_REVISION) is not None


class TestGetDatabaseState:
    def test_empty(self, sqlite_engine, head_revision):
        assert get_database_state(sqlite_engine, head_revision) is DatabaseState.EMPTY

    def test_tables_without_revision_are_unversioned(self, sqlite_engine, head_revision):
        create_table(sqlite_engine, "nodes")
        assert get_database_state(sqlite_engine, head_revision) is DatabaseState.UNVERSIONED

    def test_old_revision_is_outdated(self, sqlite_engine, head_revision):
        stamp(sqlite_engine, "0000")
        assert get_database_state(sqlite_engine, head_revision) is DatabaseState.OUTDATED

    def test_head_revision_is_current(self, sqlite_engine, head_revision):
        stamp(sqlite_engine, head_revision)
        assert get_database_state(sqlite_engine, head_revision) is DatabaseState.CURRENT


class TestEnsureDatabaseReady:
    @pytest.fixture
    def calls(self, monkeypatch):
        calls = []
        monkeypatch.setattr(database_bootstrap, "upgrade", lambda: calls.append("upgrade"))
        monkeypatch.setattr("neteye.user.models.initialize_roles", lambda: calls.append("roles"))
        monkeypatch.setattr("neteye.user.models.initialize_admin", lambda: calls.append("admin"))
        return calls

    def use_state(self, monkeypatch, state):
        monkeypatch.setattr(database_bootstrap, "get_database_state", lambda engine, head: state)

    def test_empty_database_is_migrated_and_seeded(self, app, monkeypatch, calls):
        self.use_state(monkeypatch, DatabaseState.EMPTY)
        with app.app_context():
            ensure_database_ready()
        assert calls == ["upgrade", "roles", "admin"]

    def test_current_database_is_only_seeded(self, app, monkeypatch, calls):
        self.use_state(monkeypatch, DatabaseState.CURRENT)
        with app.app_context():
            ensure_database_ready()
        assert calls == ["roles", "admin"]

    def test_unversioned_database_refuses_and_points_to_baseline(self, app, monkeypatch, calls):
        self.use_state(monkeypatch, DatabaseState.UNVERSIONED)
        with app.app_context(), pytest.raises(DatabaseNotReadyError) as excinfo:
            ensure_database_ready()
        assert f"db stamp {BASELINE_REVISION}" in str(excinfo.value)
        assert calls == []

    def test_outdated_database_refuses_without_migrating(self, app, monkeypatch, calls):
        self.use_state(monkeypatch, DatabaseState.OUTDATED)
        with app.app_context(), pytest.raises(DatabaseNotReadyError) as excinfo:
            ensure_database_ready()
        assert "db upgrade" in str(excinfo.value)
        assert calls == []
