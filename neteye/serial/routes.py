import pandas as pd
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_security import auth_required, current_user

from datatables import ColumnDT, DataTables
from neteye.api.serial_namespace import serial_schema, serials_schema
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.node.models import Node

from .forms import SerialForm
from .models import Serial

serial_bp = bp_factory("serial")


@serial_bp.route("")
@auth_required()
def index():
    return render_template("serial/index.html")


@serial_bp.route("/data")
@auth_required()
def data():
    columns = [
        ColumnDT(Serial.id),
        ColumnDT(Node.hostname),
        ColumnDT(Serial.serial_number),
        ColumnDT(Serial.product_id),
        ColumnDT(Serial.description),
    ]
    query = db.session.query().select_from(Serial).join(Node)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    return jsonify(row_table.output_result())


@serial_bp.route("/<id>")
@auth_required()
def show(id):
    serial = Serial.query.get(id)
    node = Node.query.get(serial.node_id)
    return render_template("serial/show.html", serial=serial, node=node)


@serial_bp.route("/new")
@auth_required()
def new():
    form = SerialForm()
    return render_template("serial/new.html", form=form)


@serial_bp.route("/create", methods=["POST"])
@auth_required()
def create():
    serial = Serial(
        node_id=request.form["node_id"],
        serial_number=request.form["serial_number"],
        product_id=request.form["product_id"],
        description=request.form["description"]
    )
    serial.add()
    return redirect(url_for("serial.index"))


@serial_bp.route("/<id>/edit")
@auth_required()
def edit(id):
    serial = Serial.query.get(id)
    form = SerialForm()
    node_id = serial.node_id
    serial_number = serial.serial_number
    product_id = serial.product_id
    description = serial.description
    return render_template(
        "serial/edit.html",
        id=id,
        form=form,
        node_id=node_id,
        serial_number=serial_number,
        product_id=product_id,
        description=description,
    )


@serial_bp.route("/<id>/update", methods=["POST"])
@auth_required()
def update(id):
    serial = Serial.query.get(id)
    serial.node_id = request.form["node_id"]
    serial.serial_number = request.form["serial_number"]
    serial.product_id = request.form["product_id"]
    serial.description = request.form["description"]
    serial.commit()
    return redirect(url_for("serial.show", id=id))



@serial_bp.route("/<id>/delete", methods=["POST"])
@auth_required()
def delete(id):
    serial = Serial.query.get(id)
    serial.delete()
    return redirect(url_for("serial.index"))


@serial_bp.route("/filter")
@auth_required()
def filter():
    page = request.args.get("page", 1, type=int)
    field = request.args.get("field")
    filter_str = request.args.get("filter_str")
    if field == "serial":
        serials = Serial.query.filter(Serial.serial_number.contains(filter_str))
    elif field == "product_id":
        serials = Serial.query.filter(Serial.product_id.contains(filter_str))
    elif field == "node":
        serials = (
            Serial.query.join(Node, Serial.node_id == Node.id)
            .add_columns(Serial.id, Node.hostname, Serial.serial, Serial.product_id)
            .filter(Node.hostname.contains(filter_str))
        )
    return render_template("serial/index.html", serials=serials)
