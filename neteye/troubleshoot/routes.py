import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for
from flask_security import auth_required

from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.node.models import Node

from .forms import PingForm

troubleshoot_bp = bp_factory("troubleshoot")


@troubleshoot_bp.route("/ping")
@auth_required()
def ping():
    form = PingForm()
    return render_template("/troubleshoot/ping.html", form=form)


@troubleshoot_bp.route("/ping", methods=["POST"])
@auth_required()
def ping_execute():
    return render_template("/troubleshoot/ping.html")
