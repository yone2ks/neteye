import os

_TEST_DB = "/tmp/neteye_test.db"
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)

os.environ["ENV_FOR_DYNACONF"] = "testing"

import pytest
from flask_security import hash_password
from neteye import app as flask_app
from neteye.extensions import db as _db
from neteye.user.models import user_datastore

TEST_ADMIN_EMAIL = "test_admin@example.com"
TEST_ADMIN_PASSWORD = "Test-Admin-Pass-1!"


@pytest.fixture(scope="session")
def app():
    return flask_app


@pytest.fixture(scope="session", autouse=True)
def seed_test_db(app):
    with app.app_context():
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
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app):
    with app.test_client() as c:
        c.post(
            "/login",
            data={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
        )
        yield c


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()
