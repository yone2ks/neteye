from logging import getLogger

import pandas as pd
from flask import flash, jsonify, redirect, render_template, request, session, url_for
from flask_security import auth_required, current_user
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError

from datatables import ColumnDT, DataTables
from neteye.apis.cable_namespace import cable_schema, cables_schema
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.interface.models import Interface
from neteye.node.models import Node
from neteye.lib.utils.integrity_error_utils import gen_integrity_error_message

from .forms import CableForm
from .models import Cable

logger = getLogger(__name__)

cable_bp = bp_factory("cable")
a_interface_table = aliased(Interface)
b_interface_table = aliased(Interface)
a_node_table = aliased(Node)
b_node_table = aliased(Node)


@cable_bp.route("")
@auth_required()
def index():
    return render_template("cable/index.html")

@cable_bp.route("/data")
@auth_required()
def data():
    columns = [
        ColumnDT(Cable.id),
        ColumnDT(a_node_table.hostname),
        ColumnDT(a_interface_table.name),
        ColumnDT(b_node_table.hostname),
        ColumnDT(b_interface_table.name),
        ColumnDT(Cable.cable_type),
        ColumnDT(Cable.link_speed),
        ColumnDT(Cable.description),
    ]
    query = (
        db.session.query()
        .select_from(Cable)
        .join(a_interface_table, Cable.a_interface_id == a_interface_table.id)
        .join(a_node_table, a_interface_table.node_id == a_node_table.id)
        .join(b_interface_table, Cable.b_interface_id == b_interface_table.id)
        .join(b_node_table, b_interface_table.node_id == b_node_table.id)
    )
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    return jsonify(row_table.output_result())


@cable_bp.route("/new")
@auth_required()
def new():
    form = CableForm()
    a_node = None
    b_node = None
    a_interface = None
    b_interface = None
    cable_type = None
    link_speed = None
    description = None
    return render_template(
        "cable/new.html",
        form=form,
        a_node=a_node,
        b_node=b_node,
        a_interface=a_interface,
        b_interface=b_interface,
        cable_type=cable_type,
        link_speed=link_speed,
        description=description,
    )


@cable_bp.route("/create", methods=["POST"])
@auth_required()
def create():
    cable = Cable(
        a_interface_id=request.form["a_interface"],
        b_interface_id=request.form["b_interface"],
        cable_type=request.form["cable_type"],
        link_speed=request.form["link_speed"],
        description=request.form["description"],
    )
    try:
        cable.add()
    except IntegrityError as e:
        cable.rollback()
        logger.warning(f"IntegrityError: {e}")
        flash(gen_integrity_error_message("Cable", e), "danger")
        return redirect(url_for("cable.new"))
    except Exception as e:
        cable.rollback()
        logger.error(f"Unexpected Error: {e}")
        flash("An unexpected error occurred while creating the cable.", "danger")
        return redirect(url_for("cable.new"))
    return redirect(url_for("cable.index"))


@cable_bp.route("/<id>/edit")
@auth_required()
def edit(id):
    cable = Cable.query.get(id)
    form = CableForm()
    a_interface = cable.a_interface
    b_interface = cable.b_interface
    cable_type = cable.cable_type
    link_speed = cable.link_speed
    return render_template(
        "cable/edit.html",
        id=id,
        form=form,
        a_node_id=a_interface.node_id,
        b_node_id=b_interface.node_id,
        a_interface_id=a_interface.id,
        b_interface_id=b_interface.id,
        cable_type=cable_type,
        link_speed=link_speed,
    )


@cable_bp.route("/<id>/update", methods=["POST"])
@auth_required()
def update(id):
    cable = Cable.query.get(id)
    cable.a_interface_id = request.form["a_interface"]
    cable.b_interface_id = request.form["b_interface"]
    cable.cable_type = request.form["cable_type"]
    cable.link_speed = request.form["link_speed"]
    try:
        cable.commit()
    except IntegrityError as e:
        cable.rollback()
        logger.warning(f"IntegrityError: {e}")
        flash(gen_integrity_error_message("Cable", e), "danger")
        return redirect(url_for("cable.edit", id=id))
    except Exception as e:
        cable.rollback()
        logger.error(f"Unexpected Error: {e}")
        flash("An unexpected error occurred while updating the cable.", "danger")
        return redirect(url_for("cable.edit", id=id))
    return redirect(url_for("cable.index"))


@cable_bp.route("/<id>/delete", methods=["POST"])
@auth_required()
def delete(id):
    cable = Cable.query.get(id)
    cable.delete()
    return redirect(url_for("cable.index"))
