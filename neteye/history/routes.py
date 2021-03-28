from logging import debug, error, info, warning

import netmiko
import pandas as pd
from flask import flash, redirect, render_template, request, session, url_for
from netaddr import *
from sqlalchemy.sql import exists

from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db, ntc_template_utils, settings

from .models import (OPERATION_TYPE, arp_entry_transaction, arp_entry_version,
                     cable_transaction, cable_version, interface_transaction,
                     interface_version, node_transaction, node_version,
                     serial_transaction, serial_version)

history_bp = bp_factory("history")


@history_bp.route("/node_history")
def node_history():
    node_history = db.session.query(node_version, node_transaction).filter(node_version.transaction_id == node_transaction.id).all()
    return render_template("history/node_history.html", node_history=node_history, OPERATION_TYPE=OPERATION_TYPE)


@history_bp.route("/interface_history")
def interface_history():
    interface_history = db.session.query(interface_version, interface_transaction).filter(interface_version.transaction_id == interface_transaction.id).all()
    return render_template("history/interface_history.html", interface_history=interface_history, OPERATION_TYPE=OPERATION_TYPE)


@history_bp.route("/serial_history")
def serial_history():
    serial_history = db.session.query(serial_version, serial_transaction).filter(serial_version.transaction_id == serial_transaction.id).all()
    return render_template("history/serial_history.html", serial_history=serial_history, OPERATION_TYPE=OPERATION_TYPE)


@history_bp.route("/cable_history")
def cable_history():
    cable_history = db.session.query(cable_version, cable_transaction).filter(cable_version.transaction_id == cable_transaction.id).all()
    return render_template("history/cable_history.html", cable_history=cable_history, OPERATION_TYPE=OPERATION_TYPE)


@history_bp.route("/arp_entry_history")
def arp_entry_history():
    arp_entry_history = db.session.query(arp_entry_version, arp_entry_transaction).filter(arp_entry_version.transaction_id == arp_entry_transaction.id).all()
    return render_template("history/arp_entry_history.html", arp_entry_history=arp_entry_history, OPERATION_TYPE=OPERATION_TYPE)
