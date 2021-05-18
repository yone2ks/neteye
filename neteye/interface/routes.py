import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for

from neteye.apis.interface_namespace import interface_schema, interfaces_schema
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.node.models import Node

from .forms import InterfaceForm
from .models import Interface

interface_bp = bp_factory("interface")

@interface_bp.route("")
def index():
    interfaces = Interface.query.all()
    data=interfaces_schema.dump(interfaces)
    return render_template("interface/index.html", interfaces=interfaces, data=data)


@interface_bp.route("/<id>")
def show(id):
    interface = Interface.query.get(id)
    node = Node.query.get(interface.node_id)
    return render_template("interface/show.html", interface=interface, node=node)


@interface_bp.route("/new")
def new():
    form = InterfaceForm()
    return render_template("interface/new.html", form=form)


@interface_bp.route("/create", methods=["POST"])
def create():
    interface = Interface(
        node_id=request.form["node_id"],
        name=request.form["name"],
        description=request.form["description"],
        ip_address=request.form["ip_address"],
        mask=request.form["mask"],
        speed=request.form["speed"],
        duplex=request.form["duplex"],
        mtu=request.form["mtu"],
        status=request.form["status"],
    )
    interface.add()
    return redirect(url_for("interface.index"))


@interface_bp.route("/<id>/edit")
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
def update(id):
    interface = Interface.query.get(id)
    interface.node_id = request.form["node_id"]
    interface.name = request.form["name"]
    interface.description = request.form["description"]
    interface.ip_address = request.form["ip_address"]
    interface.mask = request.form["mask"]
    interface.speed = request.form["speed"]
    interface.duplex = request.form["duplex"]
    interface.mtu = request.form["mtu"]
    interface.status = request.form["status"]
    interface.commit()
    return redirect(url_for("interface.show", id=id))


@interface_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    interface = Interface.query.get(id)
    interface.delete()
    return redirect(url_for("interface.index"))


@interface_bp.route("/filter")
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
