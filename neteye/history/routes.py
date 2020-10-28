from logging import debug, error, info, warning

import netmiko
import pandas as pd
from flask import flash, redirect, render_template, request, session, url_for
from netaddr import *
from sqlalchemy.sql import exists
from sqlalchemy_continuum import version_class

from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db, ntc_template_utils, settings
from neteye.node.models import Node
from neteye.serial.models import Serial

history_bp = bp_factory("history")

OPERATION_TYPE = {0: "INSERT", 1: "UPDATE", 2: "DELETE"}

@history_bp.route("/node_history")
def node_history():
    node_version = version_class(Node)
    node_history = db.session.query(node_version).all()
    return render_template("history/node_history.html", node_history=node_history, OPERATION_TYPE=OPERATION_TYPE)

@history_bp.route("/serial_history")
def serial_history():
    serial_version = version_class(Serial)
    serial_history = db.session.query(serial_version).all()
    return render_template("history/serial_history.html", serial_history=serial_history, OPERATION_TYPE=OPERATION_TYPE)
