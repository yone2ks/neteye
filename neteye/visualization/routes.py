import json
from logging import debug, error, info, warning

import pandas as pd
from flask import flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import aliased
from sqlalchemy.sql import exists

from neteye.arp_entry.models import ArpEntry
from neteye.blueprints import bp_factory
from neteye.cable.models import Cable
from neteye.extensions import connection_pool, db, settings
from neteye.interface.models import Interface
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from neteye.node.models import Node
from neteye.serial.models import Serial

visualization_bp = bp_factory("visualization")
src_interface_table = aliased(Interface)
dst_interface_table = aliased(Interface)
src_node_table = aliased(Node)
dst_node_table = aliased(Node)

intf_conv = IntfAbbrevConverter("cisco_ios")


@visualization_bp.route("/layer1")
def layer1():
    cables = (
        Cable.query.join(
            src_interface_table, Cable.src_interface_id == src_interface_table.id
        )
        .add_columns(src_interface_table.name)
        .join(src_node_table, src_interface_table.node_id == src_node_table.id)
        .join(dst_interface_table, Cable.dst_interface_id == dst_interface_table.id)
        .join(dst_node_table, dst_interface_table.node_id == dst_node_table.id)
        .add_columns(
            Cable.id,
            src_node_table.id.label("src_node_id"),
            src_node_table.hostname.label("src_node_hostname"),
            src_interface_table.id.label("src_interface_id"),
            src_interface_table.name.label("src_interface_name"),
            dst_node_table.id.label("dst_node_id"),
            dst_node_table.hostname.label("dst_node_hostname"),
            dst_interface_table.id.label("dst_interface_id"),
            dst_interface_table.name.label("dst_interface_name"),
            Cable.cable_type,
            Cable.link_speed,
        )
        .all()
    )
    nodes = Node.query.all()

    elements = []
    for node in nodes:
        elements.append({"group": "nodes", "data": {"id": node.hostname}, "classes": "node"})
        for interface in node.interfaces:
            elements.append({"group": "nodes", "data": {"id": interface.id, "name": intf_conv.to_abbrev(interface.name), "parent": node.hostname}, "classes": "interface"})

    for cable in cables:
        elements.append(
            {
                "group": "edges",
                "data": {
                    "id": cable.src_node_hostname + "_to_" + cable.dst_node_hostname,
                    "source": cable.src_interface_id,
                    "source_label": intf_conv.to_abbrev(cable.src_interface_name),
                    "target": cable.dst_interface_id,
                    "target_label": intf_conv.to_abbrev(cable.dst_interface_name),
                },
            }
        )

    return render_template("/visualization/layer1.html", elements=elements)
