from types import SimpleNamespace
from unittest.mock import patch

import pytest

from neteye.arp_entry.models import ArpEntry
from neteye.extensions import db as _db
from neteye.interface.models import Interface
from neteye.node.models import Node
from neteye.node.routes import import_arp_entries

ARP_COMMAND = "show ip arp vrf all"


def _arp_row(ip_address, interface, mac_address="0011.2233.4455"):
    return {
        "ip_address": ip_address,
        "mac_address": mac_address,
        "interface": interface,
        "age": "00:01:00",
        "protocol": "Internet",
        "type": "ARPA",
    }


@pytest.fixture
def two_nodes(app):
    """Two NX-OS nodes that both have Vlan10 and Ethernet1/1 registered."""
    with app.app_context():
        node_ids = {}
        for name, ip_address in (("arp-scope-a", "192.168.98.1"), ("arp-scope-b", "192.168.98.2")):
            node = Node(
                hostname=name,
                ip_address=ip_address,
                port=22,
                device_type="cisco_nxos",
                username="admin",
                password="pass",
            )
            _db.session.add(node)
            _db.session.commit()
            node_ids[name] = node.id
            for interface_name in ("Vlan10", "Ethernet1/1"):
                _db.session.add(Interface(node_id=node.id, name=interface_name))
            _db.session.commit()
    yield node_ids
    with app.app_context():
        for node_id in node_ids.values():
            interface_ids = [i.id for i in Interface.query.filter_by(node_id=node_id).all()]
            for arp in ArpEntry.query.filter(ArpEntry.interface_id.in_(interface_ids)).all():
                _db.session.delete(arp)
            for interface in Interface.query.filter_by(node_id=node_id).all():
                _db.session.delete(interface)
            node = _db.session.get(Node, node_id)
            if node:
                _db.session.delete(node)
        _db.session.commit()


def _import_arp(node_id, rows):
    def fake_command(self, command, user):
        return rows if command == ARP_COMMAND else []

    node = _db.session.get(Node, node_id)
    with patch("neteye.node.models.Node.command", fake_command), patch(
        "neteye.node.routes.current_user", SimpleNamespace(email="test@example.com")
    ):
        import_arp_entries(node)


def _arp_by_ip(node_id):
    entries = ArpEntry.query.join(Interface).filter(Interface.node_id == node_id).all()
    return {entry.ip_address: entry.interface.name for entry in entries}


def test_arp_entries_link_to_the_interface_of_the_imported_node(app, two_nodes):
    with app.app_context():
        # Node A is registered first, so an unscoped lookup would pick A's Vlan10.
        _import_arp(two_nodes["arp-scope-b"], [_arp_row("10.0.0.2", "Vlan10")])

        assert _arp_by_ip(two_nodes["arp-scope-b"]) == {"10.0.0.2": "Vlan10"}
        assert _arp_by_ip(two_nodes["arp-scope-a"]) == {}


def test_importing_one_node_does_not_remove_the_other_nodes_arp_entries(app, two_nodes):
    with app.app_context():
        _import_arp(two_nodes["arp-scope-a"], [_arp_row("10.0.0.1", "Vlan10")])
        _import_arp(two_nodes["arp-scope-b"], [_arp_row("10.0.0.2", "Vlan10")])
        _import_arp(two_nodes["arp-scope-a"], [_arp_row("10.0.0.1", "Vlan10")])

        assert _arp_by_ip(two_nodes["arp-scope-a"]) == {"10.0.0.1": "Vlan10"}
        assert _arp_by_ip(two_nodes["arp-scope-b"]) == {"10.0.0.2": "Vlan10"}


def test_abbreviated_interface_name_matches_the_registered_name(app, two_nodes):
    with app.app_context():
        _import_arp(two_nodes["arp-scope-a"], [_arp_row("10.0.1.1", "Eth1/1")])

        assert _arp_by_ip(two_nodes["arp-scope-a"]) == {"10.0.1.1": "Ethernet1/1"}


def test_record_with_unregistered_interface_is_skipped_not_fatal(app, two_nodes):
    with app.app_context():
        _import_arp(
            two_nodes["arp-scope-a"],
            [
                _arp_row("10.0.2.1", "Vlan999"),
                _arp_row("10.0.2.2", "Vlan10"),
            ],
        )

        assert _arp_by_ip(two_nodes["arp-scope-a"]) == {"10.0.2.2": "Vlan10"}


def test_record_without_interface_is_skipped_not_fatal(app, two_nodes):
    with app.app_context():
        _import_arp(
            two_nodes["arp-scope-a"],
            [
                _arp_row("10.0.3.1", ""),
                _arp_row("10.0.3.2", "Vlan10"),
            ],
        )

        assert _arp_by_ip(two_nodes["arp-scope-a"]) == {"10.0.3.2": "Vlan10"}


def test_interface_registered_only_on_another_node_is_not_used(app, two_nodes):
    with app.app_context():
        extra = Interface(node_id=two_nodes["arp-scope-a"], name="Vlan77")
        _db.session.add(extra)
        _db.session.commit()

        _import_arp(two_nodes["arp-scope-b"], [_arp_row("10.0.4.1", "Vlan77")])

        assert _arp_by_ip(two_nodes["arp-scope-b"]) == {}
