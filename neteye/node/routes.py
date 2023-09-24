from logging import debug, error, info, warning

import netmiko
import pandas as pd
import sqlalchemy
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_security import auth_required
from netaddr import *
from sqlalchemy.sql import exists

from datatables import ColumnDT, DataTables
from neteye.apis.node_namespace import node_schema, nodes_schema
from neteye.arp_entry.models import ArpEntry
from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db, ntc_template_utils, settings
from neteye.interface.models import Interface
from neteye.lib.import_command_mapper.import_command_mapper import \
    ImportCommandMapper
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from neteye.lib.utils.neteye_differ import delta_commit
from neteye.serial.models import Serial

from .forms import NodeForm
from .models import NAPALM_DRIVERS, NETMIKO_PLATFORMS, SCRAPLI_DRIVERS, Node

root_bp = bp_factory("")
node_bp = bp_factory("node")

@root_bp.route("/")
@node_bp.route("")
@auth_required()
def index():
    return render_template("node/index.html")


@node_bp.route("/data")
def data():
    columns = [
        ColumnDT(Node.id),
        ColumnDT(Node.hostname),
        ColumnDT(Node.description),
        ColumnDT(Node.ip_address),
        ColumnDT(Node.device_type),
        ColumnDT(Node.model),
        ColumnDT(Node.os_version),
    ]
    query = db.session.query().select_from(Node)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    return jsonify(row_table.output_result())


@node_bp.route("/<id>")
def show(id):
    node = Node.query.get(id)
    command_list = ntc_template_utils.get_command_list(node.device_type)
    return render_template("node/show.html", node=node, command_list=command_list)


@node_bp.route("/new")
def new():
    form = NodeForm()
    hostname = None
    description = None
    ip_address = None
    port = None
    device_type = "autodetect"
    username = None
    password = None
    enable = None
    device_type_datalist = NETMIKO_PLATFORMS
    return render_template(
        "node/new.html",
        form=form,
        hostname=hostname,
        description=description,
        ip_address=ip_address,
        port=port,
        device_type=device_type,
        username=username,
        password=password,
        enable=enable,
        device_type_datalist=device_type_datalist,
    )


@node_bp.route("/create", methods=["POST"])
def create():
    form = NodeForm()
    hostname=request.form["hostname"]
    description=request.form["description"]
    ip_address=request.form["ip_address"]
    port=request.form["port"]
    device_type=request.form["device_type"]
    username=request.form["username"]
    password=request.form["password"]
    enable=request.form["enable"]
    if form.validate_on_submit():
        node = Node(
            hostname=hostname,
            description=description,
            ip_address=ip_address,
            port=port,
            device_type=device_type,
            username=username,
            password=password,
            enable=enable,
        )
        node.add()
        return redirect(url_for("node.index"))
    else:
        device_type_datalist = NETMIKO_PLATFORMS
        return render_template(
            "node/new.html",
            form=form,
            hostname=hostname,
            description=description,
            ip_address=ip_address,
            port=port,
            device_type=device_type,
            username=username,
            password=password,
            enable=enable,
            device_type_datalist=device_type_datalist,
        )


@node_bp.route("/<id>/edit")
def edit(id):
    node = Node.query.get(id)
    form = NodeForm()
    hostname = node.hostname
    description = node.description
    ip_address = node.ip_address
    port = node.port
    device_type = node.device_type
    napalm_driver = node.napalm_driver
    scrapli_driver = node.scrapli_driver
    model = node.model
    os_type = node.os_type
    os_version = node.os_version
    username = node.username
    password = node.password
    enable = node.enable
    device_type_datalist = NETMIKO_PLATFORMS
    napalm_driver_datalist = NAPALM_DRIVERS
    scrapli_driver_datalist = SCRAPLI_DRIVERS
    return render_template(
        "node/edit.html",
        id=id,
        form=form,
        hostname=hostname,
        description=description,
        ip_address=ip_address,
        port=port,
        device_type=device_type,
        napalm_driver=napalm_driver,
        scrapli_driver=scrapli_driver,
        model=model,
        os_type=os_type,
        os_version=os_version,
        username=username,
        password=password,
        enable=enable,
        device_type_datalist=device_type_datalist,
        napalm_driver_datalist=napalm_driver_datalist,
        scrapli_driver_datalist=scrapli_driver_datalist,
    )


@node_bp.route("/<id>/update", methods=["POST"])
def update(id):
    form = NodeForm()
    hostname = request.form["hostname"]
    description = request.form["description"]
    ip_address = request.form["ip_address"]
    port = request.form["port"]
    device_type = request.form["device_type"]
    napalm_driver = request.form["napalm_driver"]
    scrapli_driver = request.form["scrapli_driver"]
    model = request.form["model"]
    os_type = request.form["os_type"]
    os_version = request.form["os_version"]
    username = request.form["username"]
    password = request.form["password"]
    enable = request.form["enable"]
    if form.validate_on_submit():
        node = Node.query.get(id)
        node.hostname = hostname
        node.description = description
        node.ip_address = ip_address
        node.port = port
        node.device_type = device_type
        node.napalm_driver = napalm_driver
        node.scrapli_driver = scrapli_driver
        node.model = model
        node.os_type = os_type
        node.os_version = os_version
        node.username = username
        node.password = password
        node.enable = enable
        node.commit()
        return redirect(url_for("node.show", id=id))
    else:
        device_type_datalist = NETMIKO_PLATFORMS
        napalm_driver_datalist = NAPALM_DRIVERS
        scrapli_driver_datalist = SCRAPLI_DRIVERS
        return render_template(
            "node/edit.html",
            id=id,
            form=form,
            hostname=hostname,
            description=description,
            ip_address=ip_address,
            port=port,
            device_type=device_type,
            napalm_driver=napalm_driver,
            scrapli_driver=scrapli_driver,
            model=model,
            os_type=os_type,
            os_version=os_version,
            username=username,
            password=password,
            enable=enable,
            device_type_datalist=device_type_datalist,
            napalm_driver_datalist=napalm_driver_datalist,
            scrapli_driver_datalist=scrapli_driver_datalist,
        )


@node_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    node = Node.query.get(id)
    node.delete()
    return redirect(url_for("node.index"))


@node_bp.route("/filter")
def filter():
    field = request.args.get("field")
    filter_str = request.args.get("filter_str")
    if field == "hostname":
        nodes = Node.query.filter(Node.hostname.contains(filter_str))
    elif field == "ip_address":
        nodes = Node.query.filter(Node.ip_address.contains(filter_str))
    return render_template("node/index.html", nodes=nodes)


@node_bp.route("/<id>/show_run")
def show_run(id):
    command = "show run"
    node = Node.query.get(id)
    result = node.raw_command(command)
    result = result.replace("\r\n", "<br />").replace("\n", "<br />")
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/show_inventory")
def show_inventory(id):
    command = "show inventory"
    node = Node.query.get(id)
    result = node.command(command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/show_version")
def show_version(id):
    command = "show version"
    node = Node.query.get(id)
    result = node.command(command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/show_ip_int_brief")
def show_ip_int_breif(id):
    command = "show ip int brief"
    node = Node.query.get(id)
    result = node.command(command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/show_interfaces_description")
def show_interfaces_description(id):
    command = "show int desc"
    node = Node.query.get(id)
    result = node.command(command)
    return render_template("node/parsed_command.html", result=result, command=command)

@node_bp.route("/<id>/show_ip_arp")
def show_ip_arp(id):
    command = "show ip arp"
    node = Node.query.get(id)
    result = node.command(command)
    return render_template("node/show_ip_arp.html", result=result, command=command)


@node_bp.route("/<id>/show_ip_route")
def show_ip_route(id):
    command = "show ip route"
    node = Node.query.get(id)
    result = node.command(command)
    return render_template("node/show_ip_route.html", result=result, command=command)


@node_bp.route("/<id>/command/<command>")
def command(id, command):
    command = command.replace("_", " ")
    node = Node.query.get(id)
    result = node.command(command)
    if isinstance(result, str):
        result = result.replace("\r\n", "<br />").replace("\n", "<br />")
        return render_template("node/command.html", result=result, command=command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/raw_command/<command>")
def raw_command(id, command):
    command = command.replace("_", " ")
    node = Node.query.get(id)
    result = node.raw_command(command).replace("\r\n", "<br />").replace("\n", "<br />")
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/netmiko/<command>")
def netmiko_command(id, command):
    command = command.replace("_", " ")
    node = Node.query.get(id)
    result = node.netmiko_command(command)
    if isinstance(result, str):
        result = result.replace("\r\n", "<br />").replace("\n", "<br />")
        return render_template("node/command.html", result=result, command=command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/raw_netmiko/<command>")
def netmiko_raw_command(id, command):
    command = command.replace("_", " ")
    node = Node.query.get(id)
    result = node.netmiko_raw_command(command).replace("\r\n", "<br />").replace("\n", "<br />")
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/scrapli/<command>")
def scrapli_command(id, command):
    command = command.replace("_", " ")
    node = Node.query.get(id)
    result = node.scrapli_command(command)
    if isinstance(result, str):
        result = result.replace("\r\n", "<br />").replace("\n", "<br />")
        return render_template("node/command.html", result=result, command=command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/raw_scrapli/<command>")
def scrapli_raw_command(id, command):
    command = command.replace("_", " ")
    node = Node.query.get(id)
    result = node.scrapli_raw_command(command).replace("\r\n", "<br />").replace("\n", "<br />")
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/napalm/get_facts")
def napalm_get_facts(id):
    node = Node.query.get(id)
    result = node.napalm_get_facts()
    return render_template("node/napalm.html", result=result, command="napalm_get_facts")


@node_bp.route("/<id>/napalm/get_interfaces")
def napalm_get_interfaces(id):
    node = Node.query.get(id)
    result = node.napalm_get_interfaces()
    return render_template("node/parsed_command.html", result=result, command="napalm_get_interfaces")


@node_bp.route("/import_node_from_id/<id>")
def import_node_from_id(id):
    try:
        node = Node.query.get(id)
        import_target_node(node)
        return redirect(url_for("node.show", id=id))
    except Exception as err:
        error("Error: Import Node {id}, {err}".format(id=id, err=err))
        return redirect(url_for("node.index"))


@node_bp.route("/import_node_from_ip/<ip_address>")
def import_node_from_ip(ip_address):
    try:
        node = try_connect_node(ip_address)
        import_target_node(node)
        return redirect(url_for("node.index"))
    except Exception as err:
        error(
            "Error: Import Node {ip_address}, {err}".format(
                ip_address=ip_address, err=err
            )
        )
        return redirect(url_for("node.index"))


@node_bp.route("/explore_node/<id>")
def explore_node(id):
    node = Node.query.get(id)
    explore_network(node)
    return redirect(url_for("node.index"))


def explore_network(node):
    command = "show ip arp"
    show_ip_arp = [
        entry
        for entry in node.command(command)
        if entry["age"] != "-"
    ]
    ng_node = []
    for arp_entry in show_ip_arp:
        if not arp_entry["address"] in ng_node:
            if not db.session.query(
                exists().where(Interface.ip_address == arp_entry["address"])
            ).scalar():
                try:
                    target_node = try_connect_node(arp_entry["address"])
                    import_target_node(target_node)
                    explore_network(target_node)
                except Exception as err:
                    ng_node.append(arp_entry["address"])
                    print(err)


def try_connect_node(ip_address):
    for cred in settings["default"]["credentials"].values():
        try:
            node = Node(
                hostname="hostname",
                ip_address=ip_address,
                port=22,
                device_type = "autodetect",
                username=cred["USERNAME"],
                password=cred["PASSWORD"],
                enable=cred["ENABLE"],
            )
            return node
        except (
            netmiko.ssh_exception.NetMikoTimeoutException,
            netmiko.ssh_exception.SSHException,
            ValueError
        ) as err:
            print(err)
            continue
        except Exception as err:
            print(
                "Err: {err}, ip_address: {ip_address}".format(
                    err=err, ip_address=ip_address
                )
            )
            break
    raise Exception


def import_serial(node):
    import_command_mapper = ImportCommandMapper(node.device_type)
    after_serials = set()
    after = dict()
    for import_command in import_command_mapper.mapping_dict["import_serial"]:
        before_serials = {serial.serial_number for serial in node.serials}
        before_field = {"serial_number", "product_id"}
        before = {serial.serial_number: {
            "id": serial.id,
            "node_id": serial.node_id,
            "serial_number": serial.serial_number,
            "product_id": serial.product_id}
                  for serial in node.serials}

        result = node.command(import_command["command"])
        if "serial_number" in import_command["field"]:
            after_serials = {serial_info[import_command["field"]["serial_number"]] for serial_info in result}
        else:
            after_serials = before_serials
        after_field = set(import_command["field"])
        delta_field = before_field - after_field
        for serial_info in result:
            after_entry = {"node_id": node.id}
            for field_name in import_command["field"]:
                after_entry[field_name] = serial_info[import_command["field"][field_name]]
            for field_name in delta_field:
                if serial_info[import_command["field"]["serial_number"]] in before:
                    after_entry[field_name] = before[serial_info[import_command["field"]["serial_number"]]][field_name]
                else:
                    after_entry[field_name] = None
            after[serial_info[import_command["field"]["serial_number"]]] = after_entry

        delta_commit(model=Serial, before_keys=before_serials, before=before, after_keys=after_serials, after=after)


def import_node(node):
    import_command_mapper = ImportCommandMapper(node.device_type)
    for import_command in import_command_mapper.mapping_dict["import_node"]:
        result = node.command(import_command["command"])
        for field_name in import_command["field"]:
            setattr(node, field_name, result[import_command["index"]][import_command["field"][field_name]])
    node.commit()


def import_interface(node):
    intf_conv = IntfAbbrevConverter(node.device_type)
    import_command_mapper = ImportCommandMapper(node.device_type)
    after_interfaces = set()
    after = dict()
    for import_command in import_command_mapper.mapping_dict["import_interface"]:
        before_interfaces = {interface.name for interface in node.interfaces}
        before_field = {"name", "ip_address", "description", "status"}
        before = {interface.name: {
            "id": interface.id,
            "node_id": interface.node_id,
            "name": interface.name,
            "ip_address": interface.ip_address,
            "description": interface.description,
            "status": interface.status}
                  for interface in node.interfaces}

        result = node.command(import_command["command"])
        if "name" in import_command["field"]:
            after_interfaces = {intf_conv.normalization(interface_info[import_command["field"]["name"]]) for interface_info in result}
        else:
            after_interfaces = before_interfaces
        after_field = set(import_command["field"])
        delta_field = before_field - after_field
        for interface_info in result:
            after_entry = {"node_id": node.id}
            for field_name in import_command["field"]:
                if field_name == "name":
                    after_entry[field_name] = intf_conv.normalization(interface_info[import_command["field"][field_name]])
                else:
                    after_entry[field_name] = interface_info[import_command["field"][field_name]]
            for field_name in delta_field:
                if intf_conv.normalization(interface_info[import_command["field"]["name"]]) in before:
                    after_entry[field_name] = before[intf_conv.normalization(interface_info[import_command["field"]["name"]])][field_name]
                else:
                    after_entry[field_name] = None

            after[intf_conv.normalization(interface_info[import_command["field"]["name"]])] = after_entry

        delta_commit(model=Interface, before_keys=before_interfaces, before=before, after_keys=after_interfaces, after=after)


def import_arp_entry(node):
    intf_conv = IntfAbbrevConverter(node.device_type)
    import_command_mapper = ImportCommandMapper(node.device_type)
    after_arp_entries = set()
    after = dict()
    before_interface_ids = {interface.id for interface in node.interfaces}

    for interface_id in before_interface_ids:
        for import_command in import_command_mapper.mapping_dict["import_arp_entry"]:
            before_field = {"ip_address", "mac_address", "protocol", "arp_type", "vendor"}
            arp_entries = ArpEntry.query.filter(ArpEntry.interface_id == interface_id).all()
            before_arp_entries = set()
            before = dict()
            if arp_entries:
                for arp_entry in arp_entries:
                    before_arp_entries.add(arp_entry.ip_address)
                    before[arp_entry.ip_address] = {
                        "id": arp_entry.id,
                        "ip_address": arp_entry.ip_address,
                        "mac_address": arp_entry.mac_address,
                        "interface_id": arp_entry.interface_id,
                        "protocol": arp_entry.protocol,
                        "arp_type": arp_entry.arp_type,
                        "vendor": arp_entry.vendor}

            result = node.command(import_command["command"])
            after_arp_entries = {arp_entry_info[import_command["field"]["ip_address"]] for arp_entry_info in result}
            after_field = set(import_command["field"])
            delta_field = before_field - after_field
            for arp_entry_info in result:
                after_entry = {"interface_id": interface_id}
                for field_name in import_command["field"]:
                        after_entry[field_name] = arp_entry_info[import_command["field"][field_name]]
                for field_name in delta_field:
                    if arp_entry_info[import_command["field"]["ip_address"]] in before:
                        after_entry[field_name] = before[arp_entry_info[import_command["field"]["ip_address"]]][field_name]
                    else:
                        after_entry[field_name] = None

                after[arp_entry_info[import_command["field"]["ip_address"]]] = after_entry

            delta_commit(model=ArpEntry, before_keys=before_arp_entries, before=before, after_keys=after_arp_entries, after=after)


def import_target_node(node):
    import_node(node)
    import_serial(node)
    import_interface(node)
    import_arp_entry(node)
