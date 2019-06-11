from neteye.extensions import db
from neteye.blueprints import bp_factory
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from flask import request, redirect, url_for, render_template, flash, session
from sqlalchemy.sql import exists
import netmiko
import pandas as pd
from dynaconf import settings
from .models import Node
from .forms import NodeForm
from neteye.interface.models import Interface
from neteye.serial.models import Serial

node_bp = bp_factory('node')

@node_bp.route('')
def index():
    page = request.args.get('page', 1, type=int)
    nodes = Node.query.paginate(page, settings.PER_PAGE)
    return render_template('node/index.html', nodes=nodes)

@node_bp.route('/<id>')
def show(id):
    node = Node.query.get(id)
    return render_template('node/show.html', node=node)

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
    return render_template('node/new.html', form=form, hostname=hostname, description=description, ip_address=ip_address, username=username, password=password, enable=enable)

@node_bp.route('/create', methods=['POST'])
def create():
    node = Node(hostname=request.form['hostname'], description=request.form['description'], ip_address=request.form['ip_address'], username=request.form['username'], password=request.form['password'], enable=request.form['enable'])
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
    return render_template('node/edit.html', id=id, form=form, hostname=hostname, description=description, ip_address=ip_address)

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
    node = Node.query.get(id)
    db.session.delete(node)
    db.session.commit()
    return redirect(url_for('node.index'))

@node_bp.route('/filter')
def filter():
    field = request.args.get('field')
    filter_str = request.args.get('filter_str')
    if field == 'hostname':
        nodes = Node.query.filter(Node.hostname.contains(filter_str))
    elif field == 'ip_address':
        nodes = Node.query.filter(Node.ip_address.contains(filter_str))
    return render_template('node/index.html', nodes=nodes)

@node_bp.route('/<id>/show_inventory')
def show_inventory(id):
    command = 'show inventory'
    node = Node.query.get(id)
    conn = node.gen_conn()
    conn.enable()
    result = conn.send_command(command, use_textfsm=True)
    for serial_info in result:
        if not db.session.query(exists().where(Serial.serial==serial_info['sn'])).scalar():
            serial = Serial(node_id=node.id, serial=serial_info['sn'], product_id=serial_info['pid'])
            db.session.add(serial)
            db.session.commit()
    return render_template('node/command.html', result=pd.DataFrame(result).to_html(table_id='result',classes='table table-responsive-sm table-hover table-outline table-striped mb-0 dataTable table-bordered'), command=command)

@node_bp.route('/<id>/show_version')
def show_version(id):
    command = 'show version'
    node = Node.query.get(id)
    conn = node.gen_conn()
    conn.enable()
    result = conn.send_command(command, use_textfsm=True)
    node.os_version = result[0]['version']
    db.session.commit()
    return render_template('node/command.html', result=pd.DataFrame(result).to_html(table_id='result',classes='table table-striped'), command=command)

@node_bp.route('/<id>/show_ip_int_brief')
def show_ip_int_breif(id):
    command = 'show ip int brief'
    node = Node.query.get(id)
    conn = node.gen_conn()
    conn.enable()
    result = conn.send_command(command, use_textfsm=True)
    for interface_info in result:
        if not db.session.query(exists().where(Interface.node_id==node.id).where(Interface.name==interface_info['intf'])).scalar():
            interface = Interface(node_id=node.id, name=interface_info['intf'], ip_address=interface_info['ipaddr'], status=interface_info['status'], description="")
            db.session.add(interface)
            db.session.commit()
    return render_template('node/command.html', result=pd.DataFrame(result).to_html(table_id='result',classes='table table-striped'), command=command)

@node_bp.route('/<id>/show_interfaces_description')
def show_interfaces_description(id):
    command = 'show interfaces description'
    node = Node.query.get(id)
    conn = node.gen_conn()
    conn.enable()
    result = conn.send_command(command, use_textfsm=True)
    intf_conv = IntfAbbrevConverter('cisco_ios')
    for interface_info in result:
        if db.session.query(exists().where(Interface.node_id==node.id).where(Interface.name==intf_conv.to_long(interface_info['port']))).scalar():
            interface = Interface.query.filter(Interface.node_id==node.id, Interface.name==intf_conv.to_long(interface_info['port'])).first()
            interface.description = interface_info['descrip']
            print(interface.id)
            db.session.commit()
    return render_template('node/command.html', result=pd.DataFrame(result).to_html(table_id='result',classes='table table-striped'), command=command)

@node_bp.route('/<id>/show_ip_arp')
def show_ip_arp(id):
    command = 'show ip arp'
    node = Node.query.get(id)
    conn = node.gen_conn()
    result = conn.send_command(command, use_textfsm=True)
    return render_template('node/show_ip_arp.html', result=result, command=command)

@node_bp.route('/<id>/show_ip_route')
def show_ip_route(id):
    command = 'show ip route'
    node = Node.query.get(id)
    conn = node.gen_conn()
    result = conn.send_command(command, use_textfsm=True)
    return render_template('node/show_ip_route.html', result=result, command=command)

@node_bp.route('/import_node/<ip_address>')
def import_node(ip_address):
    node = Node(hostname='hostname', ip_address=ip_address, username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD, enable=settings.DEFAULT_ENABLE)
    conn = node.gen_conn()
    conn.enable()
    show_inventory = conn.send_command('show inventory', use_textfsm=True)
    node.serial = show_inventory[0]['sn']
    node.model = show_inventory[0]['pid']
    show_version = conn.send_command('show version', use_textfsm=True)
    node.os_version = show_version[0]['version']
    node.hostname = show_version[0]['hostname']
    node.description = show_version[0]['hostname']
    db.session.add(node)
    db.session.commit()
    result = conn.send_command('show ip int brief', use_textfsm=True)
    for interface_info in result:
        if not db.session.query(exists().where(Interface.node_id==node.id).where(Interface.name==interface_info['intf'])).scalar():
            interface = Interface(node_id=node.id, name=interface_info['intf'], ip_address=interface_info['ipaddr'], status=interface_info['status'])
            db.session.add(interface)
            db.session.commit()
    return redirect(url_for('node.index'))

