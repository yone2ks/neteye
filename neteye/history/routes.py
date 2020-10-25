from logging import debug, error, info, warning

import netmiko
import pandas as pd
from flask import flash, redirect, render_template, request, session, url_for
from netaddr import *
from sqlalchemy.sql import exists

from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db, ntc_template_utils, settings

from .models import TransactionHistory

history_bp = bp_factory("history")

@history_bp("/transaction_history")
def index():
    transaction_history = TransactionHistory.query.all()
    return render_template("history/transaction_history.html", transaction_history=transaction_history)
