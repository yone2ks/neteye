from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import Interface
from .forms import InterfaceForm
from neteye.node.models import Node
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
from dynaconf import settings

troubleshoot_bp = bp_factory('troubleshoot')

@troubleshoot_bp.route('/ping')
def ping():
    pass


