import re

import pytest
from neteye.extensions import db as _db
from neteye.node.models import Node


@pytest.fixture
def sample_node(app):
    """ルートテスト用ノード。セットアップ・クリーンアップの前後で app context を閉じる。"""
    with app.app_context():
        node = Node(
            hostname="route-test",
            ip_address="192.168.99.1",
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


class TestNodeFilterValidation:
    def test_valid_field_hostname(self, auth_client):
        resp = auth_client.get("/node/filter?field=hostname&filter_str=router")
        assert resp.status_code == 200

    def test_valid_field_ip_address(self, auth_client):
        resp = auth_client.get("/node/filter?field=ip_address&filter_str=192.168")
        assert resp.status_code == 200

    def test_invalid_field_returns_400(self, auth_client):
        resp = auth_client.get("/node/filter?field=password&filter_str=secret")
        assert resp.status_code == 400

    def test_unknown_field_returns_400(self, auth_client):
        resp = auth_client.get("/node/filter?field=__class__&filter_str=x")
        assert resp.status_code == 400


class TestNodeCrudRoutes:
    def test_index_returns_200(self, auth_client):
        resp = auth_client.get("/node")
        assert resp.status_code == 200

    def test_show_returns_200(self, auth_client, sample_node):
        resp = auth_client.get(f"/node/{sample_node}")
        assert resp.status_code == 200

    def test_new_page_returns_200(self, auth_client):
        resp = auth_client.get("/node/new")
        assert resp.status_code == 200


class TestNodeCommandRoutes:
    """User-supplied commands must be POST-only (CSRF) and output HTML-escaped (XSS)."""

    @pytest.fixture
    def executed_commands(self, monkeypatch):
        executed = []

        def fake_command(node, command, session_user=None):
            executed.append(command)
            return "line1 <script>alert(1)</script>\nline2"

        def fake_parsed_command(node, command, session_user=None):
            executed.append(command)
            return [{"intf": "<b>Gi0/1</b>"}]

        monkeypatch.setattr(Node, "raw_command", fake_command)
        monkeypatch.setattr(Node, "command", fake_parsed_command)
        return executed

    def test_raw_command_post_escapes_output(self, auth_client, sample_node, executed_commands):
        resp = auth_client.post(f"/node/{sample_node}/raw_command", data={"command": "show run"})
        assert resp.status_code == 200
        assert executed_commands == ["show run"]
        body = resp.get_data(as_text=True)
        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;alert(1)&lt;/script&gt;<br />line2" in body

    def test_command_post_renders_parsed_result(self, auth_client, sample_node, executed_commands):
        resp = auth_client.post(f"/node/{sample_node}/command", data={"command": "show ip int brief"})
        assert resp.status_code == 200
        assert executed_commands == ["show ip int brief"]
        assert "<b>Gi0/1</b>" not in resp.get_data(as_text=True)

    @pytest.mark.parametrize("path", ["command", "raw_command", "netmiko", "raw_netmiko", "scrapli", "raw_scrapli"])
    def test_get_is_not_allowed(self, auth_client, sample_node, executed_commands, path):
        resp = auth_client.get(f"/node/{sample_node}/{path}")
        assert resp.status_code == 405
        assert executed_commands == []

    def test_legacy_get_url_no_longer_executes(self, auth_client, sample_node, executed_commands):
        resp = auth_client.get(f"/node/{sample_node}/raw_command/show+run")
        assert resp.status_code == 404
        assert executed_commands == []

    def test_empty_command_is_rejected(self, auth_client, sample_node, executed_commands):
        resp = auth_client.post(f"/node/{sample_node}/raw_command", data={"command": "  "})
        assert resp.status_code == 302
        assert executed_commands == []

    def test_post_without_csrf_token_is_rejected(self, app, auth_client, sample_node, executed_commands, monkeypatch):
        # The testing environment disables CSRF; restore the production behaviour.
        monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
        monkeypatch.setitem(app.config, "SECURITY_CSRF_PROTECT_MECHANISMS", ["session", "basic"])
        resp = auth_client.post(f"/node/{sample_node}/raw_command", data={"command": "reload"})
        assert resp.status_code == 400
        assert executed_commands == []

    def test_post_with_csrf_token_from_show_page_succeeds(self, app, auth_client, sample_node, executed_commands, monkeypatch):
        monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
        monkeypatch.setitem(app.config, "SECURITY_CSRF_PROTECT_MECHANISMS", ["session", "basic"])
        body = auth_client.get(f"/node/{sample_node}").get_data(as_text=True)
        csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', body).group(1)
        resp = auth_client.post(
            f"/node/{sample_node}/raw_command",
            data={"command": "show run", "csrf_token": csrf_token},
        )
        assert resp.status_code == 200
        assert executed_commands == ["show run"]

    def test_show_page_posts_command_form(self, auth_client, sample_node):
        body = auth_client.get(f"/node/{sample_node}").get_data(as_text=True)
        assert f'action="/node/{sample_node}/command"' in body
        assert f'formaction="/node/{sample_node}/raw_command"' in body
        assert 'name="csrf_token"' in body
