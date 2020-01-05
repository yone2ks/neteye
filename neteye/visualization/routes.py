import json
from neteye.extensions import db, connection_pool, settings
from neteye.blueprints import bp_factory
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from flask import request, redirect, url_for, render_template, flash, session
from logging import error, warning, info, debug
from sqlalchemy.sql import exists
import netmiko
import pandas as pd
from netaddr import *
from neteye.node.models import Node
from neteye.interface.models import Interface
from neteye.serial.models import Serial
from neteye.cable.models import Cable
from neteye.arp_entry.models import ArpEntry
from sqlalchemy.orm import aliased

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
        elements.append({"group": "nodes", "data": {"id": node.hostname}})
    for cable in cables:
        elements.append(
            {
                "group": "edges",
                "data": {
                    "id": cable.src_node_hostname + "_to_" + cable.dst_node_hostname,
                    "source": cable.src_node_hostname,
                    "source_label": intf_conv.to_abbrev(cable.src_interface_name),
                    "target": cable.dst_node_hostname,
                    "target_label": intf_conv.to_abbrev(cable.dst_interface_name),
                },
            }
        )

    return render_template("/visualization/layer1.html", elements=elements)
