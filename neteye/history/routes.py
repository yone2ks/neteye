import json
import datetime
from logging import debug, error, info, warning

import pandas as pd
from dateutil import parser, tz
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from sqlalchemy.sql import exists

from datatables import ColumnDT, DataTables
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
from .model_command_history import CommandHistory

history_bp = bp_factory("history")

@history_bp.route("/node_history")
def node_history():
    return render_template("history/node_history.html")


@history_bp.route("/node_history_data")
def node_history_data():
    columns = [
        ColumnDT(node_transaction.issued_at),
        ColumnDT(node_version.id),
        ColumnDT(node_version.hostname),
        ColumnDT(node_version.description),
        ColumnDT(node_version.ip_address),
        ColumnDT(node_version.device_type),
        ColumnDT(node_version.model),
        ColumnDT(node_version.os_type),
        ColumnDT(node_version.os_version),
        ColumnDT(node_version.username),
        ColumnDT(node_version.operation_type),
    ]
    query = db.session.query(node_transaction.issued_at,
                             node_version.id,
                             node_version.hostname,
                             node_version.description,
                             node_version.ip_address,
                             node_version.device_type,
                             node_version.model,
                             node_version.os_type,
                             node_version.os_version,
                             node_version.username,
                             node_version.operation_type).join(node_version, node_version.transaction_id == node_transaction.id)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    for row in row_table.output_result()["data"]:
        row['0'] = row['0'].replace(tzinfo=datetime.timezone.utc).astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        row['10'] = OPERATION_TYPE[row['10']]
    return jsonify(row_table.output_result())


@history_bp.route("/interface_history")
def interface_history():
    return render_template("history/interface_history.html")


@history_bp.route("/interface_history_data")
def interface_history_data():
    columns = [
        ColumnDT(interface_transaction.issued_at),
        ColumnDT(interface_version.id),
        ColumnDT(interface_version.node_id),
        ColumnDT(interface_version.name),
        ColumnDT(interface_version.ip_address),
        ColumnDT(interface_version.description),
        ColumnDT(interface_version.operation_type),
    ]
    query = db.session.query(interface_transaction.issued_at,
                             interface_version.id,
                             interface_version.node_id,
                             interface_version.name,
                             interface_version.ip_address,
                             interface_version.description,
                             interface_version.operation_type).join(interface_version, interface_version.transaction_id == interface_transaction.id)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    for row in row_table.output_result()["data"]:
        row['0'] = row['0'].replace(tzinfo=datetime.timezone.utc).astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        row['6'] = OPERATION_TYPE[row['6']]
    return jsonify(row_table.output_result())


@history_bp.route("/serial_history")
def serial_history():
    return render_template("history/serial_history.html")

@history_bp.route("/serial_history_data")
def serial_history_data():
    columns = [
        ColumnDT(serial_transaction.issued_at),
        ColumnDT(serial_version.id),
        ColumnDT(serial_version.node_id),
        ColumnDT(serial_version.serial_number),
        ColumnDT(serial_version.product_id),
        ColumnDT(serial_version.operation_type),
    ]
    query = db.session.query(serial_transaction.issued_at,
                             serial_version.id,
                             serial_version.node_id,
                             serial_version.serial_number,
                             serial_version.product_id,
                             serial_version.operation_type).join(serial_version, serial_version.transaction_id == serial_transaction.id)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    for row in row_table.output_result()["data"]:
        row['0'] = row['0'].replace(tzinfo=datetime.timezone.utc).astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        row['5'] = OPERATION_TYPE[row['5']]
    return jsonify(row_table.output_result())



@history_bp.route("/cable_history")
def cable_history():
    return render_template("history/cable_history.html")


@history_bp.route("/cable_history_data")
def cable_history_data():
    columns = [
        ColumnDT(cable_transaction.issued_at),
        ColumnDT(cable_version.id),
        ColumnDT(cable_version.src_interface_id),
        ColumnDT(cable_version.dst_interface_id),
        ColumnDT(cable_version.description),
        ColumnDT(cable_version.cable_type),
        ColumnDT(cable_version.link_speed),
        ColumnDT(cable_version.operation_type),
    ]
    query = db.session.query(cable_transaction.issued_at,
                             cable_version.id,
                             cable_version.src_interface_id,
                             cable_version.dst_interface_id,
                             cable_version.description,
                             cable_version.cable_type,
                             cable_version.link_speed,
                             cable_version.operation_type).join(cable_version, cable_version.transaction_id == cable_transaction.id)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    for row in row_table.output_result()["data"]:
        row['0'] = row['0'].replace(tzinfo=datetime.timezone.utc).astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        row['7'] = OPERATION_TYPE[row['7']]
    return jsonify(row_table.output_result())


@history_bp.route("/arp_entry_history")
def arp_entry_history():
    return render_template("history/arp_entry_history.html")


@history_bp.route("/arp_entry_history_data")
def arp_entry_history_data():
    columns = [
        ColumnDT(arp_entry_transaction.issued_at),
        ColumnDT(arp_entry_version.id),
        ColumnDT(arp_entry_version.ip_address),
        ColumnDT(arp_entry_version.mac_address),
        ColumnDT(arp_entry_version.interface_id),
        ColumnDT(arp_entry_version.protocol),
        ColumnDT(arp_entry_version.arp_type),
        ColumnDT(arp_entry_version.vendor),
        ColumnDT(arp_entry_version.operation_type),
    ]
    query = db.session.query(arp_entry_transaction.issued_at,
                             arp_entry_version.id,
                             arp_entry_version.ip_address,
                             arp_entry_version.mac_address,
                             arp_entry_version.interface_id,
                             arp_entry_version.protocol,
                             arp_entry_version.arp_type,
                             arp_entry_version.vendor,
                             arp_entry_version.operation_type).join(arp_entry_version, arp_entry_version.transaction_id == arp_entry_transaction.id)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    for row in row_table.output_result()["data"]:
        row['0'] = row['0'].replace(tzinfo=datetime.timezone.utc).astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        row['8'] = OPERATION_TYPE[row['8']]
    return jsonify(row_table.output_result())

@history_bp.route("/command_history")
def command_history():
    return render_template("history/command_history.html")


@history_bp.route("/command_history_data")
def command_history_data():
    columns = [
        ColumnDT(CommandHistory.created_at),
        ColumnDT(CommandHistory.node_id),
        ColumnDT(CommandHistory.hostname),
        ColumnDT(CommandHistory.command),
        ColumnDT(CommandHistory.username),
        ColumnDT(CommandHistory.id),
    ]
    query = db.session.query().select_from(CommandHistory)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    for row in row_table.output_result()["data"]:
        row['0'] = row['0'].replace(tzinfo=datetime.timezone.utc).astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
    return jsonify(row_table.output_result())

@history_bp.route("/command_history/<id>/result")
def command_history_result(id):
    command_history = CommandHistory.query.get(id)
    result = json.loads(command_history.result)
    date = command_history.created_at.replace(tzinfo=datetime.timezone.utc).astimezone(tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
    if isinstance(result, str):
        result = result.replace("\r\n", "<br />").replace("\n", "<br />")
        return render_template("history/command_result.html", result=result, command=command_history.command, hostname=command_history.hostname, username=command_history.username, date=date)
    return render_template("history/parsed_command_result.html", result=result, command=command_history.command, hostname=command_history.hostname, username=command_history.username, date=date)
