from logging import debug, error, info, warning

import netmiko
import pandas as pd
from flask import flash, redirect, render_template, request, session, url_for
from netaddr import *
from sqlalchemy.sql import exists
from sqlalchemy_continuum import transaction_class, version_class

from neteye.arp_entry.models import ArpEntry
from neteye.blueprints import bp_factory
from neteye.cable.models import Cable
from neteye.extensions import connection_pool, db, ntc_template_utils, settings
from neteye.interface.models import Interface
from neteye.node.models import Node
from neteye.serial.models import Serial

history_bp = bp_factory("history")

OPERATION_TYPE = {0: "INSERT", 1: "UPDATE", 2: "DELETE"}

@history_bp.route("/node_history")
def node_history():
    node_version = version_class(Node)
    node_transaction = transaction_class(Node)
    node_history = db.session.query(node_version, node_transaction).filter(node_version.transaction_id == node_transaction.id).all()
    return render_template("history/node_history.html", node_history=node_history, OPERATION_TYPE=OPERATION_TYPE)

@history_bp.route("/interface_history")
def interface_history():
    interface_version = version_class(Interface)
    interface_transaction = transaction_class(Interface)
    interface_history = db.session.query(interface_version, interface_transaction).filter(interface_version.transaction_id == interface_transaction.id).all()
    return render_template("history/interface_history.html", interface_history=interface_history, OPERATION_TYPE=OPERATION_TYPE)


@history_bp.route("/serial_history")
def serial_history():
    serial_version = version_class(Serial)
    serial_transaction = transaction_class(Serial)
    serial_history = db.session.query(serial_version, serial_transaction).filter(serial_version.transaction_id == serial_transaction.id).all()
    return render_template("history/serial_history.html", serial_history=serial_history, OPERATION_TYPE=OPERATION_TYPE)


@history_bp.route("/cable_history")
def cable_history():
    cable_version = version_class(Cable)
    cable_transaction = transaction_class(Cable)
    cable_history = db.session.query(cable_version, cable_transaction).filter(cable_version.transaction_id == cable_transaction.id).all()
    return render_template("history/cable_history.html", cable_history=cable_history, OPERATION_TYPE=OPERATION_TYPE)


@history_bp.route("/arp_entry_history")
def arp_entry_history():
    arp_entry_version = version_class(ArpEntry)
    arp_entry_transaction = transaction_class(ArpEntry)
    arp_entry_history = db.session.query(arp_entry_version, arp_entry_transaction).filter(arp_entry_version.transaction_id == arp_entry_transaction.id).all()
    return render_template("history/arp_entry_history.html", arp_entry_history=arp_entry_history, OPERATION_TYPE=OPERATION_TYPE)
