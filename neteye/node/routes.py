from logging import debug, error, info, warning

import netmiko
import pandas as pd
import sqlalchemy
from flask import flash, redirect, render_template, request, session, url_for
from netaddr import *
from sqlalchemy.sql import exists

from neteye.apis.node_namespace import node_schema, nodes_schema
from neteye.arp_entry.models import ArpEntry
from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db, ntc_template_utils, settings
from neteye.interface.models import Interface
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from neteye.lib.utils.neteye_differ import delta_commit
from neteye.serial.models import Serial

from .forms import NodeForm
from .models import NAPALM_DRIVERS, NETMIKO_PLATFORMS, SCRAPLI_DRIVERS, Node

node_bp = bp_factory("node")


@node_bp.route("")
def index():
    nodes = Node.query.all()
    data = nodes_schema.dump(nodes)
    return render_template("node/index.html", nodes=nodes, data=data)


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
    node = Node(
        hostname=request.form["hostname"],
        description=request.form["description"],
        ip_address=request.form["ip_address"],
        port=request.form["port"],
        device_type=request.form["device_type"],
        username=request.form["username"],
        password=request.form["password"],
        enable=request.form["enable"],
    )
    db.session.add(node)
    db.session.commit()
    return redirect(url_for("node.index"))


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
    node = Node.query.get(id)
    node.hostname = request.form["hostname"]
    node.description = request.form["description"]
    node.ip_address = request.form["ip_address"]
    node.port = request.form["port"]
    node.device_type = request.form["device_type"]
    node.napalm_driver = request.form["napalm_driver"]
    node.scrapli_driver = request.form["scrapli_driver"]
    node.model = request.form["model"]
    node.os_type = request.form["os_type"]
    node.os_version = request.form["os_version"]
    node.username = request.form["username"]
    node.password = request.form["password"]
    node.enable = request.form["enable"]
    db.session.commit()
    return redirect(url_for("node.show", id=id))


@node_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    node = Node.query.get(id)
    db.session.delete(node)
    db.session.commit()
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
    import_serial(result, node)
    import_node_model(result, node)
    return render_template(
        "node/command.html",
        result=pd.DataFrame(result).to_html(
            table_id="index",
            classes="table table-responsive-sm table-hover table-outline table-striped mt-2 mb-2 dataTable table-bordered",
        ),
        command=command,
    )


@node_bp.route("/<id>/show_version")
def show_version(id):
    command = "show version"
    node = Node.query.get(id)
    result = node.command(command)
    import_node_hostname(result, node)
    return render_template(
        "node/command.html",
        result=pd.DataFrame(result).to_html(
            table_id="index",
            classes="table table-responsive-sm table-hover table-outline table-striped mt-2 mb-2 dataTable table-bordered",
        ),
        command=command,
    )


@node_bp.route("/<id>/show_ip_int_brief")
def show_ip_int_breif(id):
    command = "show ip int brief"
    node = Node.query.get(id)
    result = node.command(command)
    import_interface(result, node)
    return render_template(
        "node/command.html",
        result=pd.DataFrame(result).to_html(
            table_id="index",
            classes="table table-responsive-sm table-hover table-outline table-striped mt-2 mb-2 dataTable table-bordered",
        ),
        command=command,
    )


@node_bp.route("/<id>/show_interfaces_description")
def show_interfaces_description(id):
    command = "show interfaces description"
    node = Node.query.get(id)
    result = node.command(command)
    # import_interface_description(result, node)
    return render_template(
        "node/command.html",
        result=pd.DataFrame(result).to_html(
            table_id="index",
            classes="table table-responsive-sm table-hover table-outline table-striped mt-2 mb-2 dataTable table-bordered",
        ),
        command=command,
    )


@node_bp.route("/<id>/show_ip_arp")
def show_ip_arp(id):
    command = "show ip arp"
    node = Node.query.get(id)
    result = node.command(command)
    import_ip_arp(result, node)
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


def import_serial(show_inventory, node):
    before_serials = [{"node_id": serial.node_id,
                       "serial_number": serial.serial_number,
                       "product_id": serial.product_id}
                      for serial in node.serials]
    after_serials = []
    for serial_info in show_inventory:
        after_serials.append({"node_id": node.id,
                              "serial_number": serial_info["sn"],
                              "product_id": serial_info["pid"]})
    delta_commit(Serial, before_serials, after_serials)


def import_node_model(show_inventory, node):
    node.model = show_inventory[0]["pid"]
    if not Node.exists(node.hostname):
        db.session.add(node)
    db.session.commit()


def import_node_hostname(show_version, node):
    node.hostname = show_version[0]["hostname"]
    node.os_version = show_version[0]["version"]
    db.session.commit()


def import_interface(show_ip_int_brief, node):
    before_interfaces = [{"node_id": interface.node_id,
                          "name": interface.name,
                          "ip_address": interface.ip_address,
                          "status": interface.status}
                         for interface in node.interfaces]
    after_interfaces = []
    for interface_info in show_ip_int_brief:
        after_interfaces.append({
            "node_id": node.id,
            "name": interface_info["intf"],
            "ip_address": interface_info["ipaddr"],
            "status": interface_info["status"]})
    delta_commit(Interface, before_interfaces, after_interfaces)


def import_interface_description(show_interfaces_description, node):
    intf_conv = IntfAbbrevConverter("cisco_ios")
    for interface_info in show_interfaces_description:
        if Interface.exists(node.id, intf_conv.to_long(interface_info["port"])):
            interface = Interface.query.filter(
                Interface.node_id == node.id,
                Interface.name == intf_conv.to_long(interface_info["port"]),
            ).first()
            interface.description = interface_info["descrip"]
            db.session.commit()


def import_ip_arp(show_ip_arp, node):
    for arp_entry_info in show_ip_arp:
        try:
            vendor = (
                EUI(arp_entry_info["mac"], dialect=mac_unix_expanded)
                .oui.registration()
                .org
            )
        except Exception as e:
            vendor = ""
        interface = Interface.query.filter(
            Interface.node_id == node.id,
            Interface.name == arp_entry_info['interface']
        ).first()
        interface_id = interface.id if interface is not None else None
        arp_entry = ArpEntry(
            ip_address=arp_entry_info["address"],
            mac_address=arp_entry_info["mac"],
            interface_id=interface_id,
            protocol=arp_entry_info["protocol"],
            arp_type=arp_entry_info["type"],
            vendor=vendor,
        )
        if not ArpEntry.exists(arp_entry_info["address"], interface_id):
            db.session.add(arp_entry)
        db.session.commit()


def import_target_node(node):
    show_inventory = node.command("show inventory")
    show_version = node.command("show version")
    import_node_hostname(show_version, node)
    import_node_model(show_inventory, node)
    import_serial(show_inventory, node)
    show_ip_int_brief = node.command("show ip int brief")
    import_interface(show_ip_int_brief, node)
    show_interfaces_description = node.command("show interfaces description")
    import_interface_description(show_interfaces_description, node)
    show_ip_arp = node.command("show ip arp")
    import_ip_arp(show_ip_arp, node)
