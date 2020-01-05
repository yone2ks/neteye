from neteye.extensions import db, connection_pool
from neteye.blueprints import bp_factory
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
from dynaconf import settings

management_bp = bp_factory("management")


@management_bp.route("/connection_pool")
def connection_pool_index():
    return render_template(
        "management/connection_pool_index.html", connection_pool=connection_pool.pool
    )


@management_bp.route("/connection_pool/<ip>/recreate")
def connection_pool_reconnect(ip):
    connection_pool.recreate_connection(ip)
    return render_template(
        "management/connection_pool_index.html", connection_pool=connection_pool.pool
    )


@management_bp.route("/connection_pool/<ip>/delete", methods=["POST"])
def connection_pool_delete(ip):
    connection_pool.delete_connection(ip)
    return render_template(
        "management/connection_pool_index.html", connection_pool=connection_pool.pool
    )
