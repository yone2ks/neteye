import importlib.util
import os

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__), "..", "migrations", "versions", "0002_rename_interfaces_to_new_abbrev.py"
)


@pytest.fixture(scope="module")
def migration():
    spec = importlib.util.spec_from_file_location("migration_0002", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "device_type,stored,expected",
    [
        ("cisco_nxos", "Port-channel10", "port-channel10"),
        ("cisco_nxos", "Loopback0", "loopback0"),
        ("cisco_nxos", "port-channel10", None),
        ("cisco_nxos", "Ethernet1/1", None),
        ("cisco_xr", "TenGigabitEthernet0/0/0/1", "TenGigE0/0/0/1"),
        ("cisco_xr", "FortyGigabitEthernet0/0/0/2.100", "FortyGigE0/0/0/2.100"),
        ("cisco_xr", "BE1", "Bundle-Ether1"),
        ("cisco_xr", "Mg0/RP0/CPU0/0", "MgmtEth0/RP0/CPU0/0"),
        ("cisco_xr", "Bundle-Ether1", None),
        ("cisco_xr", "GigabitEthernet0/0/0/0", None),
        ("cisco_ios", "Tw1/0/1", "TwoGigabitEthernet1/0/1"),
        ("cisco_ios", "Twe1/0/1", None),  # TwentyFiveGigE was already expanded by the old table
        ("cisco_ios", "Ap1/0/1", "AppGigabitEthernet1/0/1"),
        ("cisco_ios", "Nu0", "Null0"),
        ("cisco_ios", "Null0", None),
        ("cisco_xe", "Fi1/0/1", "FiveGigabitEthernet1/0/1"),
        ("cisco_ios", "Port-channel10", None),
        ("fortinet", "port1", None),
        ("cisco_nxos", "", None),
    ],
)
def test_renamed_interface(migration, device_type, stored, expected):
    assert migration.renamed_interface(device_type, stored) == expected


def test_rename_targets_match_the_current_templates(migration):
    # Each rename must equal what the current import produces for the same device output.
    # If a template changes again, rows stored under this revision's names need a new revision.
    for device_type, rules in migration.RENAME_RULES.items():
        converter = IntfAbbrevConverter(device_type)
        for abbreviation, long_name in rules["short"].items():
            assert converter.normalization(f"{abbreviation}1") == f"{long_name}1", (device_type, abbreviation)
        for new_prefix in rules["long"].values():
            assert new_prefix in converter.abbrev_to_long.values(), (device_type, new_prefix)


def test_plan_merges_a_row_whose_new_name_is_already_used(migration):
    applied, merged = migration.plan_renames("cisco_nxos", ["Port-channel10", "port-channel10", "Loopback0"])

    assert applied == {"Loopback0": "loopback0"}
    assert merged == {"Port-channel10": "port-channel10"}


def _create_tables(engine):
    metadata = sa.MetaData()
    tables = {
        "nodes": sa.Table(
            "nodes", metadata,
            sa.Column("id", sa.String, primary_key=True), sa.Column("hostname", sa.String), sa.Column("device_type", sa.String),
        ),
        "interfaces": sa.Table(
            "interfaces", metadata,
            sa.Column("id", sa.String, primary_key=True), sa.Column("node_id", sa.String), sa.Column("name", sa.String),
            sa.UniqueConstraint("node_id", "name"),
        ),
        "cables": sa.Table(
            "cables", metadata,
            sa.Column("id", sa.String, primary_key=True),
            sa.Column("a_interface_id", sa.String),
            sa.Column("b_interface_id", sa.String),
            sa.Column("sorted_interface_ids", sa.String, unique=True),
        ),
        "arp_entries": sa.Table(
            "arp_entries", metadata,
            sa.Column("id", sa.String, primary_key=True), sa.Column("interface_id", sa.String),
        ),
    }
    metadata.create_all(engine)
    return tables


def _run_upgrade(migration, connection):
    original_op = migration.op
    migration.op = Operations(MigrationContext.configure(connection))
    try:
        migration.upgrade()
    finally:
        migration.op = original_op


def test_upgrade_renames_rows_in_place(migration, tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    tables = _create_tables(engine)
    with engine.begin() as connection:
        connection.execute(sa.insert(tables["nodes"]), [
            {"id": "n1", "hostname": "nxos1", "device_type": "cisco_nxos"},
            {"id": "n2", "hostname": "ios1", "device_type": "cisco_ios"},
        ])
        connection.execute(sa.insert(tables["interfaces"]), [
            {"id": "i1", "node_id": "n1", "name": "Port-channel10"},
            {"id": "i2", "node_id": "n1", "name": "Ethernet1/1"},
            # IOS keeps "Port-channel"; only NX-OS changed.
            {"id": "i3", "node_id": "n2", "name": "Port-channel10"},
        ])
        _run_upgrade(migration, connection)
        names = dict(connection.execute(sa.select(tables["interfaces"].c.id, tables["interfaces"].c.name)).all())
    engine.dispose()

    assert names == {"i1": "port-channel10", "i2": "Ethernet1/1", "i3": "Port-channel10"}


def test_upgrade_merges_a_short_name_row_and_moves_its_cable(migration, tmp_path):
    # The old IOS table did not know "Tw", so "show int desc" stored Tw1/0/1 next to the
    # TwoGigabitEthernet1/0/1 row from "show ip int brief". The cable was made on the short row.
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    tables = _create_tables(engine)
    with engine.begin() as connection:
        connection.execute(sa.insert(tables["nodes"]), [
            {"id": "n1", "hostname": "ios1", "device_type": "cisco_ios"},
            {"id": "n2", "hostname": "ios2", "device_type": "cisco_ios"},
        ])
        connection.execute(sa.insert(tables["interfaces"]), [
            {"id": "short", "node_id": "n1", "name": "Tw1/0/1"},
            {"id": "long", "node_id": "n1", "name": "TwoGigabitEthernet1/0/1"},
            {"id": "peer", "node_id": "n2", "name": "GigabitEthernet0/1"},
            {"id": "peer2", "node_id": "n2", "name": "GigabitEthernet0/2"},
        ])
        connection.execute(sa.insert(tables["cables"]), [
            {"id": "c1", "a_interface_id": "short", "b_interface_id": "peer", "sorted_interface_ids": "peer-short"},
            # Moving c2 would duplicate c3, so it stays where it is.
            {"id": "c2", "a_interface_id": "short", "b_interface_id": "peer2", "sorted_interface_ids": "peer2-short"},
            {"id": "c3", "a_interface_id": "long", "b_interface_id": "peer2", "sorted_interface_ids": "long-peer2"},
        ])
        connection.execute(sa.insert(tables["arp_entries"]), [{"id": "a1", "interface_id": "short"}])
        _run_upgrade(migration, connection)

        interface_ids = set(connection.execute(sa.select(tables["interfaces"].c.id)).scalars())
        cables = {row.id: row for row in connection.execute(sa.select(tables["cables"])).all()}
        arp_count = connection.execute(sa.select(sa.func.count()).select_from(tables["arp_entries"])).scalar()
    engine.dispose()

    assert interface_ids == {"long", "peer", "peer2"}
    assert (cables["c1"].a_interface_id, cables["c1"].sorted_interface_ids) == ("long", "long-peer")
    assert cables["c2"].a_interface_id == "short"
    assert arp_count == 0


def test_two_rows_renamed_to_the_same_name_are_merged(migration, tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    tables = _create_tables(engine)
    with engine.begin() as connection:
        connection.execute(sa.insert(tables["nodes"]), [{"id": "n1", "hostname": "xr1", "device_type": "cisco_xr"}])
        # Neither row has the new name yet; both become MgmtEth0/RP0/CPU0/0 under the new rules.
        connection.execute(sa.insert(tables["interfaces"]), [
            {"id": "first", "node_id": "n1", "name": "Mg0/RP0/CPU0/0"},
            {"id": "second", "node_id": "n1", "name": "Mgmt0/RP0/CPU0/0"},
        ])
        original_rules = migration.RENAME_RULES["cisco_xr"]
        migration.RENAME_RULES["cisco_xr"] = {"long": {}, "short": {"Mg": "MgmtEth", "Mgmt": "MgmtEth"}}
        try:
            _run_upgrade(migration, connection)
        finally:
            migration.RENAME_RULES["cisco_xr"] = original_rules
        names = dict(connection.execute(sa.select(tables["interfaces"].c.id, tables["interfaces"].c.name)).all())
    engine.dispose()

    assert names == {"first": "MgmtEth0/RP0/CPU0/0"}
