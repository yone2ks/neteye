import datetime
from logging import debug, error, info, warning

import pandas as pd
from dateutil import parser, tz
from flask import flash, redirect, render_template, request, session, url_for
from netaddr import *
from sqlalchemy.sql import exists

from neteye.apis.history_namespace import (arp_entry_transaction_schema,
                                           arp_entry_transactions_schema,
                                           arp_entry_version_schema,
                                           arp_entry_versions_schema,
                                           cable_transaction_schema,
                                           cable_transactions_schema,
                                           cable_version_schema,
                                           cable_versions_schema,
                                           interface_transaction_schema,
                                           interface_transactions_schema,
                                           interface_version_schema,
                                           interface_versions_schema,
                                           node_transaction_schema,
                                           node_transactions_schema,
                                           node_version_schema,
                                           node_versions_schema,
                                           serial_transaction_schema,
                                           serial_transactions_schema,
                                           serial_version_schema,
                                           serial_versions_schema)
from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db, ntc_template_utils, settings

from .models import (OPERATION_TYPE, arp_entry_transaction, arp_entry_version,
                     cable_transaction, cable_version, interface_transaction,
                     interface_version, node_transaction, node_version,
                     serial_transaction, serial_version)

history_bp = bp_factory("history")


def _pretty_data(transaction_version_data):
    pretty_data = transaction_version_data.copy()
    for record in pretty_data:
        issued_at = datetime.datetime.strptime(record['issued_at'], '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
        record['issued_at'] = issued_at.astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S %Z')
        record['operation_type'] = OPERATION_TYPE[record['operation_type']]
    return pretty_data

@history_bp.route("/node_history")
def node_history():
    node_history = db.session.query(node_version, node_transaction).filter(node_version.transaction_id == node_transaction.id).all()
    data = [{**(node_transaction_schema.dump(transaction.Transaction)), **(node_version_schema.dump(transaction.NodeVersion))} for transaction in node_history]
    return render_template("history/node_history.html", data=_pretty_data(data))


@history_bp.route("/interface_history")
def interface_history():
    interface_history = db.session.query(interface_version, interface_transaction).filter(interface_version.transaction_id == interface_transaction.id).all()
    data = [{**(interface_transaction_schema.dump(transaction.Transaction)), **(interface_version_schema.dump(transaction.InterfaceVersion))} for transaction in interface_history]
    return render_template("history/interface_history.html", data=_pretty_data(data))


@history_bp.route("/serial_history")
def serial_history():
    serial_history = db.session.query(serial_version, serial_transaction).filter(serial_version.transaction_id == serial_transaction.id).all()
    data = [{**(serial_transaction_schema.dump(transaction.Transaction)), **(serial_version_schema.dump(transaction.SerialVersion))} for transaction in serial_history]
    return render_template("history/serial_history.html", data=_pretty_data(data))


@history_bp.route("/cable_history")
def cable_history():
    cable_history = db.session.query(cable_version, cable_transaction).filter(cable_version.transaction_id == cable_transaction.id).all()
    data = [{**(cable_transaction_schema.dump(transaction.Transaction)), **(cable_version_schema.dump(transaction.CableVersion))} for transaction in cable_history]
    print(data)
    return render_template("history/cable_history.html", data=_pretty_data(data))


@history_bp.route("/arp_entry_history")
def arp_entry_history():
    arp_entry_history = db.session.query(arp_entry_version, arp_entry_transaction).filter(arp_entry_version.transaction_id == arp_entry_transaction.id).all()
    data = [{**(arp_entry_transaction_schema.dump(transaction.Transaction)), **(arp_entry_version_schema.dump(transaction.ArpEntryVersion))} for transaction in arp_entry_history]
    return render_template("history/arp_entry_history.html", data=_pretty_data(data))
