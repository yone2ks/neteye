import pytest
from neteye import app as flask_app
from neteye.extensions import db as _db
from neteye.node.models import Node


@pytest.fixture
def sample_node():
    """ルートテスト用ノード。app context をテスト実行中に保持しない。"""
    with flask_app.app_context():
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
    with flask_app.app_context():
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
        # node index route is registered at /node (no trailing slash)
        resp = auth_client.get("/node")
        assert resp.status_code == 200

    def test_show_returns_200(self, auth_client, sample_node):
        # show route is /<id> (not /<id>/show)
        resp = auth_client.get(f"/node/{sample_node}")
        assert resp.status_code == 200

    def test_new_page_returns_200(self, auth_client):
        resp = auth_client.get("/node/new")
        assert resp.status_code == 200
