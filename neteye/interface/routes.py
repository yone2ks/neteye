import pandas as pd
from sqlalchemy.sql.expression import desc
from dynaconf import settings
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_security import auth_required, current_user

from datatables import ColumnDT, DataTables
from neteye.apis.interface_namespace import interface_schema, interfaces_schema
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.node.models import Node

from .forms import InterfaceForm
from .models import Interface

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
        ColumnDT(Interface.description),
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
            speed=speed,
            duplex=duplex,
            mtu=mtu,
            status=status,
        )
        interface.add()
        return redirect(url_for("interface.index"))
    else:
        return render_template(
            "interface/new.html",
            form=form,
            node_id=node_id,
            name=name,
            description=description,
            ip_address=ip_address,
            mask=mask,
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
        interface.speed = speed
        interface.duplex = duplex
        interface.mtu = mtu
        interface.status = status
        interface.commit()
        return redirect(url_for("interface.show", id=id))
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
        ).paginate(page, settings.PER_PAGE)
    elif field == "description":
        interfaces = Interface.query.filter(
            Interface.description.contains(filter_str)
        ).paginate(page, settings.PER_PAGE)
    elif field == "node":
        interfaces = (
            Interface.query.join(Node, Interface.node_id == Node.id)
            .add_columns(
                Interface.id, Node.hostname, Interface.name, Interface.ip_address
            )
            .filter(Node.hostname.contains(filter_str))
            .paginate(page, settings.PER_PAGE)
        )
    return render_template("interface/index.html", interfaces=interfaces)
