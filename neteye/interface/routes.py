from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import Interface
from .forms import InterfaceForm
from neteye.node.models import Node
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd


interface_bp = bp_factory('interface')

@interface_bp.route('')
def index():
    page = request.args.get('page', 1, type=int)
    interfaces = Interface.query.join(Node, Interface.node_id==Node.id).add_columns(Interface.id, Node.hostname, Interface.name, Interface.ip_address).paginate(page, 3)
    return render_template('interface/index.html', interfaces=interfaces)

