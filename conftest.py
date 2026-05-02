import os

# DYNACONF_ 環境変数は settings.toml をオーバーライドする。
# neteye import より前に設定することで、import 時の create_app() からテスト DB が使われる。
_TEST_DB = "/tmp/neteye_test.db"
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)

os.environ["DYNACONF_SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{_TEST_DB}"
os.environ["DYNACONF_WTF_CSRF_ENABLED"] = "false"
os.environ["DYNACONF_SECURITY_CSRF_PROTECT_MECHANISMS"] = "@json []"
os.environ["DYNACONF_SECRET_KEY"] = "test-secret-key"

import pytest
from flask_security import hash_password
from neteye import app as flask_app
from neteye.extensions import db as _db
from neteye.user.models import user_datastore

TEST_ADMIN_EMAIL = "test_admin@example.com"
TEST_ADMIN_PASSWORD = "Test-Admin-Pass-1!"


@pytest.fixture(scope="session")
def app():
    """pytest-flask 互換用。明示的に使う場合のみ。"""
    return flask_app


@pytest.fixture(scope="session", autouse=True)
def seed_test_db():
    """テスト管理者ユーザーをセッション開始時に1回だけ作成する。
    app フィクスチャに依存しないことで pytest-flask の autouse context 注入を回避する。"""
    with flask_app.app_context():
        user_datastore.create_user(
            email=TEST_ADMIN_EMAIL,
            password=hash_password(TEST_ADMIN_PASSWORD),
            roles=["admin"],
        )
        _db.session.commit()
    yield
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


@pytest.fixture
def auth_client():
    """テスト管理者としてログイン済みのクライアント。
    pytest-flask の client フィクスチャに依存しないことで autouse context 注入を回避する。"""
    with flask_app.test_client() as client:
        client.post(
            "/login",
            data={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
        )
        yield client


@pytest.fixture
def db():
    """モデルテスト用。app context を開いて DB セッションを提供する。"""
    with flask_app.app_context():
        yield _db
        _db.session.rollback()
