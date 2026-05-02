import pytest
from neteye.node.models import Node, NOT_SUPPORTED


@pytest.fixture
def cisco_ios_node(db):
    node = Node(
        hostname="test-router",
        ip_address="192.168.1.1",
        port=22,
        device_type="cisco_ios",
        username="admin",
        password="pass",
    )
    db.session.add(node)
    db.session.commit()
    yield node
    db.session.delete(node)
    db.session.commit()


class TestNodeDriverDetection:
    def test_scrapli_driver_set_for_cisco_ios(self, cisco_ios_node):
        assert cisco_ios_node.scrapli_driver is not None
        assert cisco_ios_node.scrapli_driver != NOT_SUPPORTED

    def test_napalm_driver_set_for_cisco_ios(self, cisco_ios_node):
        assert cisco_ios_node.napalm_driver is not None
        assert cisco_ios_node.napalm_driver != NOT_SUPPORTED

    def test_unknown_device_type_falls_back_to_not_supported(self, db):
        node = Node(
            hostname="unknown-device",
            ip_address="10.0.0.1",
            port=22,
            device_type="unknown_vendor_os",
            username="admin",
            password="pass",
        )
        db.session.add(node)
        db.session.commit()
        assert node.scrapli_driver == NOT_SUPPORTED
        assert node.napalm_driver == NOT_SUPPORTED
        db.session.delete(node)
        db.session.commit()


class TestNodeCrud:
    def test_get_returns_node(self, cisco_ios_node):
        found = Node.get(cisco_ios_node.id)
        assert found is not None
        assert found.hostname == "test-router"

    def test_get_returns_none_for_missing_id(self, db):
        assert Node.get("nonexistent-id") is None
