import netmiko
import pandas as pd
from dynaconf import settings
from flask import flash, redirect, render_template, request, session, url_for

from neteye.apis.arp_entry_namespace import (arp_entries_schema,
                                             arp_entry_schema)
from neteye.blueprints import bp_factory
from neteye.extensions import db
from neteye.interface.models import Interface
from neteye.node.models import Node

from .models import ArpEntry

arp_entry_bp = bp_factory("arp_entry")


@arp_entry_bp.route("")
def index():
    arp_entries = ArpEntry.query.all()
    data = arp_entries_schema.dump(arp_entries)
    return render_template("arp_entry/index.html", arp_entries=arp_entries, data=data)
