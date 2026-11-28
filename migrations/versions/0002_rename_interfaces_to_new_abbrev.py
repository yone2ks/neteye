"""rename stored interface names to the current abbreviation tables

The interface abbreviation tables changed after v1.1.0 (cisco_nxos and cisco_xr got their own
tables, and new short forms were added for IOS-family devices). An interface stored under the old
name would no longer match the name the next import produces, so the import would delete the row
and create a new one with a new id, leaving cables and ARP entries pointing at the deleted row.

This revision renames those rows in place, so their ids, cables, ARP entries and history stay.

When the new name is already stored on the node (on IOS-family devices "show int desc" gives the
short form and "show ip int brief" the long one, so the old tables stored both), the two rows are
merged instead: cables move to the row that already has the new name, ARP entries of the old row
are deleted (the next ARP import brings them back) and the old row is deleted.

The rename rules are frozen here on purpose: later edits to the templates must not change what
this revision does.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-28 12:00:00.000000

"""
import logging
import re

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

_IOS_FAMILY_RULES = {
    # The old table expanded these short forms to a different long name.
    "long": {"Ap": "AppGigabitEthernet"},
    # Short forms the old table did not know, so they were stored as they were.
    "short": {
        "Tw": "TwoGigabitEthernet",
        "Fi": "FiveGigabitEthernet",
        "Hu": "HundredGigE",
        "Nu": "Null",
    },
}

# For "long", the key is the name the old table produced (followed by a digit) and the value is
# the name the current table produces for the same device output.
# For "short", the key must be the whole leading run of letters, as IntfAbbrevConverter.is_abbrev does.
RENAME_RULES = {
    "cisco_ios": _IOS_FAMILY_RULES,
    "cisco_ios_telnet": _IOS_FAMILY_RULES,
    "cisco_xe": _IOS_FAMILY_RULES,
    "cisco_nxos": {
        "long": {"Port-channel": "port-channel", "Loopback": "loopback"},
        "short": {},
    },
    "cisco_xr": {
        "long": {"TenGigabitEthernet": "TenGigE", "FortyGigabitEthernet": "FortyGigE"},
        "short": {"Hu": "HundredGigE", "BE": "Bundle-Ether", "Mg": "MgmtEth", "Nu": "Null"},
    },
}


def renamed_interface(device_type, name):
    """Return the name the current tables give to a stored interface name, or None if it is unchanged."""
    rules = RENAME_RULES.get(device_type)
    if rules is None or not name:
        return None
    for old_prefix, new_prefix in rules["long"].items():
        rest = name[len(old_prefix):]
        if name.startswith(old_prefix) and rest[:1].isdigit():
            return new_prefix + rest
    leading_letters = re.match(r"[A-Za-z]+", name)
    if leading_letters and leading_letters.group() in rules["short"]:
        return rules["short"][leading_letters.group()] + name[leading_letters.end():]
    return None


def plan_renames(device_type, names):
    """
    Plan the renames for the interfaces of one node.

    Args:
        device_type (str): The node's device type.
        names (iterable[str]): The interface names stored for the node.

    Returns:
        tuple[dict, dict]: The renames to apply ({old: new}) and the rows to merge into an existing
            row because the new name is already used on the node ({old: new}).
    """
    names = set(names)
    renames = {}
    for name in names:
        new_name = renamed_interface(device_type, name)
        if new_name is not None:
            renames[name] = new_name
    # No rule produces a name that another rule renames again, so the stored names are enough here.
    taken = set(names)
    applied, merged = {}, {}
    for old_name, new_name in sorted(renames.items()):
        if new_name in taken:
            merged[old_name] = new_name
        else:
            applied[old_name] = new_name
            taken.add(new_name)
    return applied, merged


def _merge_interface(connection, tables, hostname, old_id, old_name, new_id, new_name):
    """Move the cables of the old interface row to the surviving row, then delete the old row."""
    interfaces, cables, arp_entries = tables
    cable_rows = connection.execute(
        sa.select(cables.c.id, cables.c.a_interface_id, cables.c.b_interface_id).where(
            sa.or_(cables.c.a_interface_id == old_id, cables.c.b_interface_id == old_id)
        )
    ).all()
    for cable_id, a_interface_id, b_interface_id in cable_rows:
        a_interface_id = new_id if a_interface_id == old_id else a_interface_id
        b_interface_id = new_id if b_interface_id == old_id else b_interface_id
        sorted_interface_ids = "-".join(sorted([a_interface_id or "", b_interface_id or ""]))
        duplicate = connection.execute(
            sa.select(cables.c.id).where(cables.c.sorted_interface_ids == sorted_interface_ids, cables.c.id != cable_id)
        ).first()
        if a_interface_id == b_interface_id or duplicate is not None:
            # Moving it would connect the interface to itself or duplicate another cable. The cable
            # is kept and shown with a missing end, so the operator can fix or delete it.
            logger.warning(
                "Cable %s on %s %s was not moved to %s: it would duplicate another cable or loop back",
                cable_id, hostname, old_name, new_name,
            )
            continue
        connection.execute(
            sa.update(cables).where(cables.c.id == cable_id).values(
                a_interface_id=a_interface_id, b_interface_id=b_interface_id, sorted_interface_ids=sorted_interface_ids
            )
        )
    connection.execute(sa.delete(arp_entries).where(arp_entries.c.interface_id == old_id))
    connection.execute(sa.delete(interfaces).where(interfaces.c.id == old_id))
    logger.info("Merged interface %s on %s into %s", old_name, hostname, new_name)


def upgrade():
    nodes = sa.table("nodes", sa.column("id", sa.String), sa.column("hostname", sa.String), sa.column("device_type", sa.String))
    interfaces = sa.table("interfaces", sa.column("id", sa.String), sa.column("node_id", sa.String), sa.column("name", sa.String))
    cables = sa.table(
        "cables",
        sa.column("id", sa.String),
        sa.column("a_interface_id", sa.String),
        sa.column("b_interface_id", sa.String),
        sa.column("sorted_interface_ids", sa.String),
    )
    arp_entries = sa.table("arp_entries", sa.column("id", sa.String), sa.column("interface_id", sa.String))
    connection = op.get_bind()

    node_rows = connection.execute(
        sa.select(nodes.c.id, nodes.c.hostname, nodes.c.device_type).where(nodes.c.device_type.in_(list(RENAME_RULES)))
    ).all()
    for node_id, hostname, device_type in node_rows:
        interface_rows = connection.execute(
            sa.select(interfaces.c.id, interfaces.c.name).where(interfaces.c.node_id == node_id)
        ).all()
        ids_by_name = {name: interface_id for interface_id, name in interface_rows}
        applied, merged = plan_renames(device_type, ids_by_name)
        # The surviving row of a merge is either stored under the new name or renamed to it below.
        surviving_ids = dict(ids_by_name)
        surviving_ids.update({new_name: ids_by_name[old_name] for old_name, new_name in applied.items()})
        for old_name, new_name in merged.items():
            _merge_interface(
                connection, (interfaces, cables, arp_entries), hostname,
                ids_by_name[old_name], old_name, surviving_ids[new_name], new_name,
            )
        for old_name, new_name in applied.items():
            connection.execute(
                sa.update(interfaces).where(interfaces.c.id == ids_by_name[old_name]).values(name=new_name)
            )
            logger.info("Renamed interface %s on %s to %s", old_name, hostname, new_name)


def downgrade():
    # The old names cannot be recovered reliably (several short forms map to one long name), and
    # the old tables do not need them: an import with the old code re-creates rows as before.
    pass
