from neteye.extensions import db
from neteye.blueprints import bp_factory
from .models import Node
from .forms import NodeForm
from flask import request, redirect, url_for, render_template, flash, session
import netmiko
import pandas as pd
import os
os.environ["NET_TEXTFSM"] = "/Users/yone2ks/Documents/Projects/neteye/neteye/ntc-templates/templates"

node_bp = bp_factory('node')

@node_bp.route('')
def index():
    nodes = Node.query.all()
    return render_template('layout.html', nodes=nodes)

@node_bp.route('/<id>')
def show(id):
    node = Node.query.get(id)
    return render_template('show.html', node=node)

@node_bp.route('/new')
def new():
    form = NodeForm()
    hostname = None
    description = None
    ip_address = None
    username = None
    password = None
    enable = None
    if form.validate_on_submit():
        hostname = form.hostname.data
        description = form.description.data
        ip_address = form.ip_address.data
        username = form.username.data
        password = form.password.data
        enable = form.enable.data
        form.hostname.data = ''
        form.description.data = ''
        form.ip_address.data = ''
        form.username.data = ''
        form.password.data = ''
        form.enable.data = ''
    return render_template('new.html', form=form, hostname=hostname, description=description, ip_address=ip_address, username=username, password=password, enable=enable)

@node_bp.route('/create', methods=['POST'])
def create():
    node = Node(hostname=request.form['hostname'], description=request.form['description'], ip_address=request.form['ip_address'])
    db.session.add(node)
    db.session.commit()
    return redirect(url_for('node.index'))

@node_bp.route('/<id>/edit')
def edit(id):
    node = Node.query.get(id)
    form = NodeForm()
    hostname = node.hostname
    description = node.description
    ip_address = node.ip_address
    if form.validate_on_submit():
        hostname = form.hostname.data
        description = form.description.data
        ip_address = form.ip_address.data
        form.hostname.data = ''
        form.description.data = ''
        form.ip_address.data = ''
    return render_template('edit.html', id=id, form=form, hostname=hostname, description=description, ip_address=ip_address)

@node_bp.route('/<id>/update', methods=['POST'])
def update(id):
    node = Node.query.get(id)
    node.hostname = request.form['hostname']
    node.description = request.form['description']
    node.ip_address = request.form['ip_address']
    node.username = request.form['username']
    node.password = request.form['password']
    node.enable = request.form['enable']
    db.session.commit()
    return redirect(url_for('node.show', id=id))


@node_bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    Node.query.get(id).delete()
    db.session.commit()
    return redirect(url_for('node.index'))


@node_bp.route('/<id>/show_ip_arp')
def show_ip_arp(id):
    node = Node.query.get(id)
    conn = node.gen_conn()
    result = conn.send_command('show ip arp', use_textfsm=True)
    return render_template('command.html', result=pd.DataFrame(result).to_html(classes='table table-striped'))

@node_bp.route('/<id>/show_inventory')
def show_inventory(id):
    node = Node.query.get(id)
    conn = node.gen_conn()
    conn.enable()
    result = conn.send_command('show inventory', use_textfsm=True)
    node.serial = result[0]['sn']
    node.os_type = result[0]['pid']
    node.os_version = result[0]['vid']
    db.session.commit()
    return render_template('command.html', result=pd.DataFrame(result).to_html(classes='table table-striped'))

