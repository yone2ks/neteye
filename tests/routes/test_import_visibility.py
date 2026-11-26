import logging
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from neteye.arp_entry.models import ArpEntry
from neteye.extensions import db as _db
from neteye.interface.models import Interface
from neteye.lib.import_command_mapper.import_command_mapper import ImportCommandMapper
from neteye.node.models import Node
from neteye.node.routes import import_arp_entries, import_interfaces

BRIEF_COMMAND = "show ip int brief vrf all"
DESCRIPTION_COMMAND = "show int desc"
ARP_COMMAND = "show ip arp vrf all"


def _brief_row(interface):
    return {"interface": interface, "ip_address": "unassigned", "status": "up"}


def _description_row(port):
    return {"port": port, "speed": "auto", "description": ""}


def _arp_row(ip_address, interface):
    return {
        "ip_address": ip_address,
        "mac_address": "0011.2233.4455",
        "interface": interface,
        "age": "00:01:00",
        "protocol": "Internet",
        "type": "ARPA",
    }


@pytest.fixture
def nxos_node(app):
    with app.app_context():
        node = Node(
            hostname="visibility-nxos",
            ip_address="192.168.96.1",
            port=22,
            device_type="cisco_nxos",
            username="admin",
            password="pass",
        )
        _db.session.add(node)
        _db.session.commit()
        node_id = node.id
    yield node_id
    with app.app_context():
        interface_ids = [i.id for i in Interface.query.filter_by(node_id=node_id).all()]
        for arp in ArpEntry.query.filter(ArpEntry.interface_id.in_(interface_ids)).all():
            _db.session.delete(arp)
        for interface in Interface.query.filter_by(node_id=node_id).all():
            _db.session.delete(interface)
        node = _db.session.get(Node, node_id)
        if node:
            _db.session.delete(node)
        _db.session.commit()


def _run(import_function, node_id, outputs):
    def fake_command(self, command, user):
        return outputs.get(command, [])

    node = _db.session.get(Node, node_id)
    with patch("neteye.node.models.Node.command", fake_command), patch(
        "neteye.node.routes.current_user", SimpleNamespace(email="test@example.com")
    ):
        return import_function(node)


def test_unexpanded_short_name_is_reported(app, nxos_node, caplog):
    with app.app_context(), caplog.at_level(logging.WARNING, logger="neteye.node.routes"):
        _run(
            import_interfaces,
            nxos_node,
            {
                BRIEF_COMMAND: [_brief_row("Ethernet1/1")],
                DESCRIPTION_COMMAND: [_description_row("Eth1/1"), _description_row("Xy7")],
            },
        )

        messages = [record.getMessage() for record in caplog.records]
        assert any("Xy7" in message and "cisco_nxos" in message for message in messages)
        # Eth1/1 is in the template and merges with the long-name row.
        assert {i.name for i in Interface.query.filter_by(node_id=nxos_node).all()} == {"Ethernet1/1", "Xy7"}


def test_expanded_names_are_not_reported(app, nxos_node, caplog):
    with app.app_context(), caplog.at_level(logging.WARNING, logger="neteye.node.routes"):
        _run(
            import_interfaces,
            nxos_node,
            {BRIEF_COMMAND: [_brief_row("Ethernet1/1")], DESCRIPTION_COMMAND: [_description_row("Eth1/1"), _description_row("Po10")]},
        )

        assert not [r for r in caplog.records if "look abbreviated" in r.getMessage()]


def test_arp_import_returns_the_number_of_skipped_records(app, nxos_node):
    with app.app_context():
        _db.session.add(Interface(node_id=nxos_node, name="Vlan10"))
        _db.session.commit()

        skipped = _run(
            import_arp_entries,
            nxos_node,
            {ARP_COMMAND: [_arp_row("10.0.0.1", "Vlan10"), _arp_row("10.0.0.2", "Vlan99"), _arp_row("10.0.0.3", "")]},
        )

        assert skipped == 2


def test_arp_import_without_skips_returns_zero(app, nxos_node):
    with app.app_context():
        _db.session.add(Interface(node_id=nxos_node, name="Vlan10"))
        _db.session.commit()

        assert _run(import_arp_entries, nxos_node, {ARP_COMMAND: [_arp_row("10.0.0.1", "Vlan10")]}) == 0


def test_mapper_loads_the_interface_template_once():
    mapper = ImportCommandMapper("cisco_nxos")
    first = mapper.get_normalizer("import_interface", "show int desc", "name")
    second = mapper.get_normalizer("import_interface", "show int desc", "name")

    assert first.__self__ is second.__self__ is mapper.interface_converter


def test_mapper_without_template_uses_the_noop_normalizer():
    mapper = ImportCommandMapper("fortinet")

    assert mapper.interface_converter is None
    assert mapper.get_normalizer("import_interface", "get system interface physical", "name")("Gi1") == "Gi1"


def test_arp_route_reports_skipped_records_as_one_warning(app, auth_client, nxos_node):
    with patch("neteye.node.routes.import_arp_entries", return_value=3):
        response = auth_client.post(f"/node/import_arp_entry/{nxos_node}", follow_redirects=True)

    page = response.get_data(as_text=True)
    assert "3 records were skipped" in page
    assert "imported successfully" not in page


def test_arp_route_reports_plain_success_without_skips(app, auth_client, nxos_node):
    with patch("neteye.node.routes.import_arp_entries", return_value=0):
        response = auth_client.post(f"/node/import_arp_entry/{nxos_node}", follow_redirects=True)

    page = response.get_data(as_text=True)
    assert "imported successfully" in page
    assert "were skipped" not in page


def test_incomplete_entry_is_imported_and_vendor_follows_the_resolved_mac(app, nxos_node):
    with app.app_context():
        _run(import_interfaces, nxos_node, {BRIEF_COMMAND: [_brief_row("Vlan10")]})
        unresolved = dict(_arp_row("10.0.10.5", "Vlan10"), mac_address="INCOMPLETE")
        _run(import_arp_entries, nxos_node, {ARP_COMMAND: [unresolved]})
        entry = ArpEntry.query.filter_by(ip_address="10.0.10.5").one()
        assert (entry.mac_address, entry.vendor) == ("Incomplete", "")

        resolved = dict(_arp_row("10.0.10.5", "Vlan10"), mac_address="0000.0c07.ac01")
        _run(import_arp_entries, nxos_node, {ARP_COMMAND: [resolved]})
        _db.session.expire_all()
        entry = ArpEntry.query.filter_by(ip_address="10.0.10.5").one()
        assert (entry.mac_address, entry.vendor) == ("0000.0c07.ac01", "Cisco Systems, Inc")

        _run(import_arp_entries, nxos_node, {ARP_COMMAND: [unresolved]})
        _db.session.expire_all()
        entry = ArpEntry.query.filter_by(ip_address="10.0.10.5").one()
        assert (entry.mac_address, entry.vendor) == ("Incomplete", "")
