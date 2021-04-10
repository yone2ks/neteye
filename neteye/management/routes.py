import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for

from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db

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
