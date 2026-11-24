import pytest

from neteye.extensions import db as _db
from neteye.interface.models import Interface
from neteye.node.models import Node


def _add_node(hostname, ip_address, device_type):
    node = Node(
        hostname=hostname,
        ip_address=ip_address,
        port=22,
        device_type=device_type,
        username="admin",
        password="pass",
    )
    _db.session.add(node)
    _db.session.commit()
    return node.id


@pytest.fixture
def nodes(app):
    """An IOS node and a node whose device type has no abbreviation template."""
    with app.app_context():
        ios_id = _add_node("exists-ios", "192.168.97.1", "cisco_ios")
        plain_id = _add_node("exists-plain", "192.168.97.2", "no_abbrev_template")
        _db.session.add(Interface(node_id=ios_id, name="Ethernet1/1"))
        _db.session.add(Interface(node_id=plain_id, name="Eth1/1"))
        _db.session.commit()
        ids = {"ios": ios_id, "plain": plain_id}
    yield ids
    with app.app_context():
        for node_id in ids.values():
            for interface in Interface.query.filter_by(node_id=node_id).all():
                _db.session.delete(interface)
            node = _db.session.get(Node, node_id)
            if node:
                _db.session.delete(node)
        _db.session.commit()


def test_exists_with_registered_name(app, nodes):
    with app.app_context():
        assert Interface.exists(nodes["ios"], "Ethernet1/1") is True


def test_exists_expands_abbreviated_name(app, nodes):
    with app.app_context():
        assert Interface.exists(nodes["ios"], "Eth1/1") is True


def test_exists_false_for_unregistered_name(app, nodes):
    with app.app_context():
        assert Interface.exists(nodes["ios"], "Ethernet9/9") is False


def test_exists_is_scoped_to_the_node(app, nodes):
    with app.app_context():
        assert Interface.exists(nodes["plain"], "Ethernet1/1") is False


def test_exists_without_abbrev_template_uses_name_as_given(app, nodes):
    with app.app_context():
        assert Interface.exists(nodes["plain"], "Eth1/1") is True


def test_exists_for_unknown_node_is_false(app):
    with app.app_context():
        assert Interface.exists("no-such-node", "Ethernet1/1") is False
