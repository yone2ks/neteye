from neteye.extensions import db
from neteye.blueprints import bp_factory
from neteye.node.models import Node
from .forms import PingForm
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
from dynaconf import settings

troubleshoot_bp = bp_factory("troubleshoot")


@troubleshoot_bp.route("/ping")
def ping():
    form = PingForm()
    return render_template("/troubleshoot/ping.html", form=form)


@troubleshoot_bp.route("/ping", methods=["POST"])
def ping_execute():
    return render_template("/troubleshoot/ping.html")
