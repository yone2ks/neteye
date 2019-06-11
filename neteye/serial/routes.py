from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import Serial
from neteye.node.models import Node
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
from dynaconf import settings

serial_bp = bp_factory('serial')

@serial_bp.route('')
def index():
    page = request.args.get('page', 1, type=int)
    serials = Serial.query.join(Node, Serial.node_id==Node.id).add_columns(Serial.id, Node.hostname, Serial.serial, Serial.product_id).paginate(page, settings.PER_PAGE)
    return render_template('serial/index.html', serials=serials)

@serial_bp.route('/filter')
def filter():
    page = request.args.get('page', 1, type=int)
    field = request.args.get('field')
    filter_str = request.args.get('filter_str')
    if field == 'serial':
        serials = Serial.query.filter(Serial.serial.contains(filter_str)).paginate(page, settings.PER_PAGE)
    elif field == 'product_id':
        serials = Serial.query.filter(Serial.product_id.contains(filter_str)).paginate(page, settings.PER_PAGE)
    elif field == 'node':
        serials = Serial.query.join(Node, Serial.node_id==Node.id).add_columns(Serial.id, Node.hostname, Serial.serial, Serial.product_id).filter(Node.hostname.contains(filter_str)).paginate(page, settings.PER_PAGE)
    return render_template('serial/index.html', serials=serials)
