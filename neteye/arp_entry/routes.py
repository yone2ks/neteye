import netmiko
import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for

from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.interface.models import Interface
from neteye.node.models import Node

from .models import ArpEntry

arp_entry_bp = bp_factory("arp_entry")


@arp_entry_bp.route("")
def index():
    arp_entries = (
        ArpEntry.query.join(Interface, ArpEntry.interface_id == Interface.id).join(Node, Interface.node_id == Node.id)
        .add_columns(
            ArpEntry.id,
            ArpEntry.ip_address,
            ArpEntry.mac_address,
            ArpEntry.vendor,
            Interface.name.label("interface"),
            Node.hostname
        )
        .all()
    )
    return render_template("arp_entry/index.html", arp_entries=arp_entries)
