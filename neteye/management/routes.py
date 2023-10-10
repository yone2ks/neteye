import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for
from flask_security import auth_required, current_user

from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db
from neteye.node.models import Node

management_bp = bp_factory("management")


@management_bp.route("/connection_pool")
@auth_required()
def connection_pool_index():
    return render_template(
        "management/connection_pool_index.html", connection_pool=connection_pool.pool
    )


@management_bp.route("/connection_pool/<ip_address>_<driver_type>/recreate")
@auth_required()
def connection_pool_reconnect(ip_address, driver_type):
    node = Node.query.filter(Node.ip_address == ip_address).first()
    connection_pool.recreate_connection(node, driver_type)
    return render_template(
        "management/connection_pool_index.html", connection_pool=connection_pool.pool
    )


@management_bp.route("/connection_pool/<ip_address>_<driver_type>/delete", methods=["POST"])
@auth_required()
def connection_pool_delete(ip_address, driver_type):
    node = Node.query.filter(Node.ip_address == ip_address).first()
    connection_pool.delete_connection(node, driver_type)
    return render_template(
        "management/connection_pool_index.html", connection_pool=connection_pool.pool
    )
