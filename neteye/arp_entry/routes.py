import pandas as pd
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_security import auth_required, current_user

from datatables import ColumnDT, DataTables
from neteye.apis.arp_entry_namespace import (arp_entries_schema,
                                             arp_entry_schema)
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.interface.models import Interface
from neteye.node.models import Node

from .models import ArpEntry

arp_entry_bp = bp_factory("arp_entry")


@arp_entry_bp.route("")
@auth_required()
def index():
    return render_template("arp_entry/index.html")


@arp_entry_bp.route("/data")
@auth_required()
def data():
    columns = [
        ColumnDT(ArpEntry.id),
        ColumnDT(ArpEntry.ip_address),
        ColumnDT(ArpEntry.mac_address),
        ColumnDT(Node.hostname),
        ColumnDT(Interface.name),
        ColumnDT(ArpEntry.vendor),
    ]
    query = db.session.query().select_from(ArpEntry).join(Interface).join(Node)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    return jsonify(row_table.output_result())
