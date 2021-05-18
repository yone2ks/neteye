import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import aliased

from neteye.apis.cable_namespace import cable_schema, cables_schema
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.interface.models import Interface
from neteye.node.models import Node

from .forms import CableForm
from .models import Cable

cable_bp = bp_factory("cable")
src_interface_table = aliased(Interface)
dst_interface_table = aliased(Interface)
src_node_table = aliased(Node)
dst_node_table = aliased(Node)


@cable_bp.route("")
def index():
    cables = Cable.query.all()
    data = cables_schema.dump(cables)
    return render_template("cable/index.html", cables=cables, data=data)


@cable_bp.route("/new")
def new():
    form = CableForm()
    src_node = None
    dst_node = None
    src_interface = None
    dst_interface = None
    cable_type = None
    link_speed = None
    description = None
    return render_template(
        "cable/new.html",
        form=form,
        src_node=src_node,
        dst_node=dst_node,
        src_interface=src_interface,
        dst_interface=dst_interface,
        cable_type=cable_type,
        link_speed=link_speed,
        description=description,
    )


@cable_bp.route("/create", methods=["POST"])
def create():
    cable = Cable(
        src_interface_id=request.form["src_interface"],
        dst_interface_id=request.form["dst_interface"],
        cable_type=request.form["cable_type"],
        link_speed=request.form["link_speed"],
        description=request.form["description"],
    )
    cable.add()
    return redirect(url_for("cable.index"))


@cable_bp.route("/<id>/edit")
def edit(id):
    cable = Cable.query.get(id)
    form = CableForm()
    src_interface = cable.src_interface
    dst_interface = cable.dst_interface
    cable_type = cable.cable_type
    link_speed = cable.link_speed
    return render_template(
        "cable/edit.html",
        id=id,
        form=form,
        src_node_id=src_interface.node_id,
        dst_node_id=dst_interface.node_id,
        src_interface_id=src_interface.id,
        dst_interface_id=dst_interface.id,
        cable_type=cable_type,
        link_speed=link_speed,
    )


@cable_bp.route("/<id>/update", methods=["POST"])
def update(id):
    cable = Cable.query.get(id)
    cable.src_interface_id = request.form["src_interface"]
    cable.dst_interface_id = request.form["dst_interface"]
    cable.cable_type = request.form["cable_type"]
    cable.link_speed = request.form["link_speed"]
    cable.commit()
    return redirect(url_for("cable.index"))


@cable_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    cable = Cable.query.get(id)
    cable.delete()
    return redirect(url_for("cable.index"))
