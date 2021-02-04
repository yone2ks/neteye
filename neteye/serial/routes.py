import netmiko
import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for

from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.node.models import Node

from .forms import SerialForm
from .models import Serial

serial_bp = bp_factory("serial")


@serial_bp.route("")
def index():
    serials = (
        Serial.query.join(Node, Serial.node_id == Node.id)
        .add_columns(Serial.id, Node.hostname, Serial.serial, Serial.product_id)
        .all()
    )
    return render_template("serial/index.html", serials=serials)

@serial_bp.route("/new")
def new():
    form = SerialForm()
    return render_template("serial/new.html", form=form)


@serial_bp.route("/create", methods=["POST"])
def create():
    serial = Serial(
        node_id=request.form["node"],
        serial=request.form["serial"],
        product_id=request.form["product_id"]
    )
    db.session.add(serial)
    db.session.commit()
    return redirect(url_for("serial.index"))


@serial_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    serial = Serial.query.get(id)
    db.session.delete(serial)
    db.session.commit()
    return redirect(url_for("serial.index"))


@serial_bp.route("/filter")
def filter():
    page = request.args.get("page", 1, type=int)
    field = request.args.get("field")
    filter_str = request.args.get("filter_str")
    if field == "serial":
        serials = Serial.query.filter(Serial.serial.contains(filter_str)).paginate(
            page, settings.PER_PAGE
        )
    elif field == "product_id":
        serials = Serial.query.filter(Serial.product_id.contains(filter_str)).paginate(
            page, settings.PER_PAGE
        )
    elif field == "node":
        serials = (
            Serial.query.join(Node, Serial.node_id == Node.id)
            .add_columns(Serial.id, Node.hostname, Serial.serial, Serial.product_id)
            .filter(Node.hostname.contains(filter_str))
            .paginate(page, settings.PER_PAGE)
        )
    return render_template("serial/index.html", serials=serials)
