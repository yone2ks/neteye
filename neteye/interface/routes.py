from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import Interface
from .forms import InterfaceForm
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
import os
os.environ["NET_TEXTFSM"] = "/Users/yone2ks/Documents/Projects/neteye/neteye/ntc-templates/templates"

interface_bp = bp_factory('interface')

@interface_bp.route('')
def index():
    interfaces = Interface.query.all()
    return render_template('interface/layout.html', interfaces=interfaces)

