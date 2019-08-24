from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import Interface
from .forms import InterfaceForm
from neteye.node.models import Node
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
from dynaconf import settings

interface_bp = bp_factory('interface')

@interface_bp.route('')
def index():
    interfaces = Interface.query.join(Node, Interface.node_id==Node.id).add_columns(Interface.id, Node.hostname, Interface.name, Interface.ip_address, Interface.description).all()
    return render_template('interface/index.html', interfaces=interfaces)

@interface_bp.route('/filter')
def filter():
    page = request.args.get('page', 1, type=int)
    field = request.args.get('field')
    filter_str = request.args.get('filter_str')
    if field == 'ip_address':
        interfaces = Interface.query.filter(Interface.ip_address.contains(filter_str)).paginate(page, settings.PER_PAGE)
    elif field == 'description':
        interfaces = Interface.query.filter(Interface.description.contains(filter_str)).paginate(page, settings.PER_PAGE)
    elif field == 'node':
        interfaces = Interface.query.join(Node, Interface.node_id==Node.id).add_columns(Interface.id, Node.hostname, Interface.name, Interface.ip_address).filter(Node.hostname.contains(filter_str)).paginate(page, settings.PER_PAGE)
    return render_template('interface/index.html', interfaces=interfaces)
