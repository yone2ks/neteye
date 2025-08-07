from logging import getLogger

import pandas as pd
from sqlalchemy.sql.expression import desc
from sqlalchemy.exc import IntegrityError
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_security import auth_required, current_user

from datatables import ColumnDT, DataTables
from neteye.apis.interface_namespace import interface_schema, interfaces_schema
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.node.models import Node
from neteye.lib.utils.integrity_error_utils import gen_integrity_error_message

from .forms import InterfaceForm
from .models import Interface

logger = getLogger(__name__)

interface_bp = bp_factory("interface")

@interface_bp.route("")
@auth_required()
def index():
    return render_template("interface/index.html")


@interface_bp.route("/data")
@auth_required()
def data():
    columns = [
        ColumnDT(Interface.id),
        ColumnDT(Node.hostname),
        ColumnDT(Interface.name),
        ColumnDT(Interface.ip_address),
        ColumnDT(Interface.mac_address),
        ColumnDT(Interface.description),
        ColumnDT(Interface.status),
    ]
    query = db.session.query().select_from(Interface).join(Node)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    return jsonify(row_table.output_result())


@interface_bp.route("/<id>")
@auth_required()
def show(id):
    interface = Interface.query.get(id)
    node = Node.query.get(interface.node_id)
    return render_template("interface/show.html", interface=interface, node=node)


@interface_bp.route("/new")
@auth_required()
def new():
    form = InterfaceForm()
    return render_template("interface/new.html", form=form)


@interface_bp.route("/create", methods=["POST"])
@auth_required()
def create():
    form = InterfaceForm()
    node_id=request.form["node_id"]
    name=request.form["name"]
    description=request.form["description"]
    ip_address=request.form["ip_address"]
    mask=request.form["mask"]
    mac_address=request.form["mac_address"]
    speed=request.form["speed"]
    duplex=request.form["duplex"]
    mtu=request.form["mtu"]
    status=request.form["status"]
    if form.validate_on_submit():
        interface = Interface(
            node_id=node_id,
            name=name,
            description=description,
            ip_address=ip_address,
            mask=mask,
            mac_address=mac_address,
            speed=speed,
            duplex=duplex,
            mtu=mtu,
            status=status,
        )
        try:
            interface.add()
            return redirect(url_for("interface.index"))
        except IntegrityError as e:
            interface.rollback()
            logger.warning(f"IntegrityError: {e}")
            flash(gen_integrity_error_message("Interface", e), "danger")
            return redirect(url_for("interface.new"))
        except Exception as e:
            interface.rollback()
            logger.error(f"Unexpected Error: {e}")
            flash("An unexpected error occurred while creating the interface.", "danger")
            return redirect(url_for("interface.new"))
    else:
        return render_template(
            "interface/new.html",
            form=form,
            node_id=node_id,
            name=name,
            description=description,
            ip_address=ip_address,
            mask=mask,
            mac_address=mac_address,
            speed=speed,
            duplex=duplex,
            mtu=mtu,
            status=status,
        )


@interface_bp.route("/<id>/edit")
@auth_required()
def edit(id):
    interface = Interface.query.get(id)
    form = InterfaceForm()
    node_id = interface.node_id
    name = interface.name
    description = interface.description
    ip_address = interface.ip_address
    mask = interface.mask
    mac_address = interface.mac_address
    speed = interface.speed
    duplex = interface.duplex
    mtu = interface.mtu
    status = interface.status
    return render_template(
        "interface/edit.html",
        id=id,
        form=form,
        node_id=node_id,
        name=name,
        description=description,
        ip_address=ip_address,
        mask=mask,
        mac_address=mac_address,
        speed=speed,
        duplex=duplex,
        mtu=mtu,
        status=status,
    )


@interface_bp.route("/<id>/update", methods=["POST"])
@auth_required()
def update(id):
    form = InterfaceForm()
    node_id = request.form["node_id"]
    name = request.form["name"]
    description = request.form["description"]
    ip_address = request.form["ip_address"]
    mask = request.form["mask"]
    mac_address = request.form["mac_address"]
    speed = request.form["speed"]
    duplex = request.form["duplex"]
    mtu = request.form["mtu"]
    status = request.form["status"]
    if form.validate_on_submit():
        interface = Interface.query.get(id)
        interface.node_id = node_id
        interface.name = name
        interface.description = description
        interface.ip_address = ip_address
        interface.mask = mask
        interface.mac_address = mac_address
        interface.speed = speed
        interface.duplex = duplex
        interface.mtu = mtu
        interface.status = status
        try:
            interface.commit()
            return redirect(url_for("interface.show", id=id))
        except IntegrityError as e:
            interface.rollback()
            logger.warning(f"IntegrityError: {e}")
            flash(gen_integrity_error_message("Interface", e), "danger")
            return redirect(url_for("interface.edit", id=id))
        except Exception as e:
            interface.rollback()
            logger.error(f"Unexpected Error: {e}")
            flash("An unexpected error occurred while updating the interface.", "danger")
            return redirect(url_for("interface.edit", id=id))
    else:
        return render_template(
            "interface/edit.html",
            id=id,
            form=form,
            node_id=node_id,
            name=name,
            description=description,
            ip_address=ip_address,
            mask=mask,
            mac_address=mac_address,
            speed=speed,
            duplex=duplex,
            mtu=mtu,
            status=status,
        )


@interface_bp.route("/<id>/delete", methods=["POST"])
@auth_required()
def delete(id):
    interface = Interface.query.get(id)
    interface.delete()
    return redirect(url_for("interface.index"))


@interface_bp.route("/filter")
@auth_required()
def filter():
    page = request.args.get("page", 1, type=int)
    field = request.args.get("field")
    filter_str = request.args.get("filter_str")
    if field == "ip_address":
        interfaces = Interface.query.filter(
            Interface.ip_address.contains(filter_str)
        )
    elif field == "description":
        interfaces = Interface.query.filter(
            Interface.description.contains(filter_str)
        )
    elif field == "node":
        interfaces = (
            Interface.query.join(Node, Interface.node_id == Node.id)
            .add_columns(
                Interface.id, Node.hostname, Interface.name, Interface.ip_address
            )
            .filter(Node.hostname.contains(filter_str))
        )
    return render_template("interface/index.html", interfaces=interfaces)
