from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import Cable
from .forms import CableForm
from neteye.node.models import Node
from neteye.interface.models import Interface
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
from dynaconf import settings
from sqlalchemy.orm import aliased


cable_bp = bp_factory('cable')
src_interface_table = aliased(Interface)
dst_interface_table = aliased(Interface)
src_node_table = aliased(Node)
dst_node_table = aliased(Node)

@cable_bp.route('')
def index():
    cables = Cable.query.join(src_interface_table, Cable.src_interface_id==src_interface_table.id)\
                        .join(src_node_table, src_interface_table.node_id == src_node_table.id)\
                        .join(dst_interface_table, Cable.dst_interface_id==dst_interface_table.id)\
                        .join(dst_node_table, dst_interface_table.node_id == dst_node_table.id)\
                        .add_columns(Cable.id, src_node_table.hostname, src_interface_table.name, dst_node_table.hostname, dst_interface_table.name, Cable.cable_type, Cable.link_speed).all()
    # import pdb; pdb.set_trace()
    # cables = Cable.query.join(Interface, Cable.src_interface_id==Interface.id)\
    #                     .join(Node, Interface.node_id == Node.id)\
    #                     .add_columns(Cable.id, Interface.name, Node.hostname, Cable.cable_type, Cable.link_speed).all()
    return render_template('cable/index.html', cables=cables)

@cable_bp.route('/new')
def new():
    form = CableForm()
    src_node = None
    dst_node = None
    src_interface = None
    dst_interface = None
    cable_type = None
    link_speed = None
    return render_template('cable/new.html', form=form, src_node=src_node, dst_node=dst_node, src_interface=src_interface, dst_interface=dst_interface, cable_type=cable_type, link_speed=link_speed)

@cable_bp.route('/create', methods=['POST'])
def create():
    cable = Cable(src_interface_id=request.form['src_interface'], dst_interface_id=request.form['dst_interface'], cable_type=request.form['cable_type'], link_speed=request.form['link_speed'])
    db.session.add(cable)
    db.session.commit()
    return redirect(url_for('cable.index'))
