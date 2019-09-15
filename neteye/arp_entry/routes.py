from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import ArpEntry
from neteye.node.models import Node
from neteye.interface.models import Interface
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
from dynaconf import settings

arp_entry_bp = bp_factory('arp_entry')

@arp_entry_bp.route('')
def index():
    arp_entries = ArpEntry.query.join(Interface, ArpEntry.interface_id==Interface.id)\
                                .add_columns(ArpEntry.id, ArpEntry.ip_address, ArpEntry.mac_address, ArpEntry.vendor, Interface.name.label('interface')).all()
    return render_template('arp_entry/index.html', arp_entries=arp_entries)

