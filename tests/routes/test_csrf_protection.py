"""CSRF must protect browser sessions but not header-based token auth.

The testing environment disables CSRF globally; these tests turn it back on
and use the configured SECURITY_CSRF_PROTECT_MECHANISMS, so they exercise
the same behaviour as development/production.
"""
import pytest
from neteye.extensions import db as _db
from neteye.node.models import Node
from neteye.user.models import User

from conftest import TEST_ADMIN_EMAIL


@pytest.fixture
def csrf_enabled(app, monkeypatch):
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)


@pytest.fixture
def api_node(app):
    with app.app_context():
        node = Node(
            hostname="csrf-test",
            ip_address="192.168.98.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="pass",
        )
        _db.session.add(node)
        _db.session.commit()
        node_id = node.id
    yield node_id
    with app.app_context():
        node = _db.session.get(Node, node_id)
        if node:
            _db.session.delete(node)
            _db.session.commit()


@pytest.fixture
def executed_commands(monkeypatch):
    executed = []

    def fake_command(node, command, session_user=None):
        executed.append(command)
        return "ok"

    monkeypatch.setattr(Node, "command", fake_command)
    return executed


@pytest.fixture
def auth_token(app):
    with app.app_context():
        return User.query.filter_by(email=TEST_ADMIN_EMAIL).first().get_auth_token()


class TestCsrfProtectMechanisms:
    def test_session_and_basic_are_protected_but_not_token(self, app):
        mechanisms = app.config["SECURITY_CSRF_PROTECT_MECHANISMS"]
        assert set(mechanisms) == {"session", "basic"}


class TestApiCsrf:
    def test_token_auth_post_does_not_require_csrf(
        self, client, csrf_enabled, api_node, executed_commands, auth_token
    ):
        resp = client.post(
            f"/api/nodes/{api_node}/command",
            json={"command": "show version"},
            headers={"Authentication-Token": auth_token},
        )
        assert resp.status_code == 200
        assert executed_commands == ["show version"]

    def test_session_auth_post_without_csrf_token_is_rejected(
        self, auth_client, csrf_enabled, api_node, executed_commands
    ):
        resp = auth_client.post(
            f"/api/nodes/{api_node}/command",
            json={"command": "show version"},
        )
        assert resp.status_code == 400
        assert executed_commands == []
