from logging import debug, error, getLogger, info

import netmiko
import pandas as pd
import sqlalchemy
from datatables import ColumnDT, DataTables
from flask import flash, jsonify, redirect, render_template, request, session, url_for
from flask_security import auth_required, current_user
from netaddr import *
from neteye.apis.node_namespace import node_schema, nodes_schema
from neteye.arp_entry.models import ArpEntry
from neteye.blueprints import bp_factory
from neteye.extensions import connection_pool, db, ntc_template_utils, settings
from neteye.interface.models import Interface
from neteye.lib.import_command_mapper.import_command_mapper import ImportCommandMapper
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from neteye.lib.utils.neteye_differ import delta_commit
from neteye.serial.models import Serial
from sqlalchemy.sql import exists

from .forms import NodeForm
from .models import NAPALM_DRIVERS, NETMIKO_PLATFORMS, SCRAPLI_DRIVERS, Node

logger = getLogger(__name__)

root_bp = bp_factory("")
node_bp = bp_factory("node")


@root_bp.route("/")
@node_bp.route("")
@auth_required()
def index():
    return render_template("node/index.html")


@node_bp.route("/data")
@auth_required()
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
@auth_required()
def show(id):
    node = Node.query.get(id)
    command_list = ntc_template_utils.get_command_list(node.device_type)
    return render_template("node/show.html", node=node, command_list=command_list)


@node_bp.route("/new")
@auth_required()
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
@auth_required()
def create():
    form = NodeForm()
    hostname = request.form["hostname"]
    description = request.form["description"]
    ip_address = request.form["ip_address"]
    port = request.form["port"]
    device_type = request.form["device_type"]
    username = request.form["username"]
    password = request.form["password"]
    enable = request.form["enable"]
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
        return redirect(url_for("node.show", id=node.id))
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
@auth_required()
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
    ntc_template_platform = node.ntc_template_platform
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
        ntc_template_platform=ntc_template_platform,
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
@auth_required()
def update(id):
    form = NodeForm()
    hostname = request.form["hostname"]
    description = request.form["description"]
    ip_address = request.form["ip_address"]
    port = request.form["port"]
    device_type = request.form["device_type"]
    napalm_driver = request.form["napalm_driver"]
    scrapli_driver = request.form["scrapli_driver"]
    ntc_template_platform = request.form["ntc_template_platform"]
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
        node.ntc_template_platform = ntc_template_platform
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
            ntc_template_platform=ntc_template_platform,
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
@auth_required()
def delete(id):
    node = Node.query.get(id)
    node.delete()
    return redirect(url_for("node.index"))


@node_bp.route("/filter")
@auth_required()
def filter():
    field = request.args.get("field")
    filter_str = request.args.get("filter_str")
    if field == "hostname":
        nodes = Node.query.filter(Node.hostname.contains(filter_str))
    elif field == "ip_address":
        nodes = Node.query.filter(Node.ip_address.contains(filter_str))
    return render_template("node/index.html", nodes=nodes)


@node_bp.route("/<id>/show+run")
@auth_required()
def show_run(id):
    command = "show run"
    node = Node.query.get(id)
    result = node.raw_command_with_history(command, current_user.email)
    result = result.replace("\r\n", "<br />").replace("\n", "<br />")
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/show+inventory")
@auth_required()
def show_inventory(id):
    command = "show inventory"
    node = Node.query.get(id)
    result = node.command_with_history(command, current_user.email)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/show+version")
@auth_required()
def show_version(id):
    command = "show version"
    node = Node.query.get(id)
    result = node.command_with_history(command, current_user.email)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/show+ip+int+brief")
@auth_required()
def show_ip_int_breif(id):
    command = "show ip int brief"
    node = Node.query.get(id)
    result = node.command_with_history(command, current_user.email)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/show+interfaces+description")
@auth_required()
def show_interfaces_description(id):
    command = "show int desc"
    node = Node.query.get(id)
    result = node.command_with_history(command, current_user.email)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/show+ip+arp")
@auth_required()
def show_ip_arp(id):
    command = "show ip arp"
    node = Node.query.get(id)
    result = node.command_with_history(command, current_user.email)
    return render_template("node/show_ip_arp.html", result=result, command=command)


@node_bp.route("/<id>/show+ip+route")
@auth_required()
def show_ip_route(id):
    command = "show ip route"
    node = Node.query.get(id)
    result = node.command_with_history(command, current_user.email)
    return render_template("node/show_ip_route.html", result=result, command=command)


@node_bp.route("/<id>/command/<command>")
@auth_required()
def command(id, command):
    command = command.replace("+", " ")
    node = Node.query.get(id)
    result = node.command_with_history(command, current_user.email)
    if isinstance(result, str):
        result = result.replace("\r\n", "<br />").replace("\n", "<br />")
        return render_template("node/command.html", result=result, command=command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/raw_command/<command>")
@auth_required()
def raw_command(id, command):
    command = command.replace("+", " ")
    node = Node.query.get(id)
    result = (
        node.raw_command_with_history(command, current_user.email)
        .replace("\r\n", "<br />")
        .replace("\n", "<br />")
    )
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/netmiko/<command>")
@auth_required()
def netmiko_command(id, command):
    command = command.replace("+", " ")
    node = Node.query.get(id)
    result = node.netmiko_command_with_history(command, current_user.email)
    if isinstance(result, str):
        result = result.replace("\r\n", "<br />").replace("\n", "<br />")
        return render_template("node/command.html", result=result, command=command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/raw_netmiko/<command>")
@auth_required()
def netmiko_raw_command(id, command):
    command = command.replace("+", " ")
    node = Node.query.get(id)
    result = (
        node.netmiko_raw_command_with_history(command, current_user.email)
        .replace("\r\n", "<br />")
        .replace("\n", "<br />")
    )
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/scrapli/<command>")
@auth_required()
def scrapli_command(id, command):
    command = command.replace("+", " ")
    node = Node.query.get(id)
    result = node.scrapli_command_with_history(command, current_user.email)
    if isinstance(result, str):
        result = result.replace("\r\n", "<br />").replace("\n", "<br />")
        return render_template("node/command.html", result=result, command=command)
    return render_template("node/parsed_command.html", result=result, command=command)


@node_bp.route("/<id>/raw_scrapli/<command>")
@auth_required()
def scrapli_raw_command(id, command):
    command = command.replace("+", " ")
    node = Node.query.get(id)
    result = (
        node.scrapli_raw_command_with_history(command, current_user.email)
        .replace("\r\n", "<br />")
        .replace("\n", "<br />")
    )
    return render_template("node/command.html", result=result, command=command)


@node_bp.route("/<id>/napalm/get_facts")
@auth_required()
def napalm_get_facts(id):
    node = Node.query.get(id)
    result = node.napalm_get_facts()
    return render_template(
        "node/napalm.html", result=result, command="napalm_get_facts"
    )


@node_bp.route("/<id>/napalm/get_interfaces")
@auth_required()
def napalm_get_interfaces(id):
    node = Node.query.get(id)
    result = node.napalm_get_interfaces()
    return render_template(
        "node/parsed_command.html", result=result, command="napalm_get_interfaces"
    )


@node_bp.route("/import_node_from_id/<id>")
@auth_required()
def import_node_from_id(id):
    try:
        node = Node.query.get(id)
        import_target_node(node)
        logger.info(f"Node {id} imported successfully")
        return redirect(url_for("node.show", id=id))
    except Exception as err:
        logger.error(f"Error importing node {id}: {str(err)}")
        return redirect(url_for("node.show", id=id))


@node_bp.route("/import_node_from_ip/<ip_address>")
@auth_required()
def import_node_from_ip(ip_address):
    try:
        node = try_connect_node(ip_address)
        import_target_node(node)
        logger.info(f"Node {ip_address} imported successfully")
        return redirect(url_for("node.index"))
    except Exception as err:
        logger.error(f"Error importing node {ip_address}: {str(err)}")
        return redirect(url_for("node.show", id=node.id))


@node_bp.route("/explore_node/<id>")
@auth_required()
def explore_node(id):
    node = Node.query.get(id)
    explore_network(node)
    return redirect(url_for("node.index"))


def explore_network(node):
    interface_ids = [interface.id for interface in node.interfaces]
    arp_entries = ArpEntry.query.filter(ArpEntry.interface_id.in_(interface_ids)).all()
    ng_node = []
    for entry in arp_entries:
        try:
            target_node = try_connect_node(entry.ip_address)
            import_target_node(target_node)
        except Exception as err:
            break


def try_connect_node(ip_address):
    for cred in settings["default"]["credentials"].values():
        try:
            logger.debug(f"Trying to connect to {ip_address}")
            node = Node(
                hostname="hostname",
                ip_address=ip_address,
                port=22,
                device_type="autodetect",
                username=cred["USERNAME"],
                password=cred["PASSWORD"],
                enable=cred["ENABLE"],
            )
            logger.info(f"Successfully connected to {ip_address}")
            return node
        except (
            netmiko.exceptions.NetMikoTimeoutException,
            netmiko.exceptions.SSHException,
            ValueError,
        ) as err:
            logger.error(f"Error connecting to {ip_address}: {str(err)}")
            continue
        except Exception as err:
            logger.error(f"Error connecting to {ip_address}: {str(err)}")
            break


def import_serial(node):
    import_command_mapper = ImportCommandMapper(node.device_type)
    after_serials = set()
    after = dict()
    for import_command in import_command_mapper.mapping_dict["import_serial"]:
        before_serials = {serial.serial_number for serial in node.serials}
        before_field = {"serial_number", "product_id"}
        before = {
            serial.serial_number: {
                "id": serial.id,
                "node_id": serial.node_id,
                "serial_number": serial.serial_number,
                "product_id": serial.product_id,
            }
            for serial in node.serials
        }

        result = node.command_with_history(
            import_command["command"], current_user.email
        )
        if isinstance(result, list):
            if "serial_number" in import_command["field"]:
                after_serials = {
                    serial_info[import_command["field"]["serial_number"]]
                    for serial_info in result
                }
            else:
                after_serials = before_serials
            after_field = set(import_command["field"])
            delta_field = before_field - after_field
            for serial_info in result:
                after_entry = {"node_id": node.id}
                for field_name in import_command["field"]:
                    after_entry[field_name] = serial_info[
                        import_command["field"][field_name]
                    ]
                for field_name in delta_field:
                    if serial_info[import_command["field"]["serial_number"]] in before:
                        after_entry[field_name] = before[
                            serial_info[import_command["field"]["serial_number"]]
                        ][field_name]
                    else:
                        after_entry[field_name] = None
                after[serial_info[import_command["field"]["serial_number"]]] = (
                    after_entry
                )

            delta_commit(
                model=Serial,
                before_keys=before_serials,
                before=before,
                after_keys=after_serials,
                after=after,
            )


def import_node(node):
    import_command_mapper = ImportCommandMapper(node.device_type)
    for import_command in import_command_mapper.mapping_dict["import_node"]:
        result = node.command_with_history(
            import_command["command"], current_user.email
        )
        if isinstance(result, list):
            for field_name in import_command["field"]:
                setattr(
                    node,
                    field_name,
                    result[import_command["index"]][
                        import_command["field"][field_name]
                    ],
                )
    node.commit()


def import_interface(node):
    intf_conv = IntfAbbrevConverter(node.device_type)
    import_command_mapper = ImportCommandMapper(node.device_type)
    after_interfaces = set()
    after = dict()
    for import_command in import_command_mapper.mapping_dict["import_interface"]:
        before_interfaces = {interface.name for interface in node.interfaces}
        before_field = {"name", "ip_address", "description", "status"}
        before = {
            interface.name: {
                "id": interface.id,
                "node_id": interface.node_id,
                "name": interface.name,
                "ip_address": interface.ip_address,
                "description": interface.description,
                "status": interface.status,
            }
            for interface in node.interfaces
        }

        result = node.command_with_history(
            import_command["command"], current_user.email
        )
        if isinstance(result, list):
            if "name" in import_command["field"]:
                after_interfaces = {
                    intf_conv.normalization(
                        interface_info[import_command["field"]["name"]]
                    )
                    for interface_info in result
                }
            else:
                after_interfaces = before_interfaces
            after_field = set(import_command["field"])
            delta_field = before_field - after_field
            for interface_info in result:
                after_entry = {"node_id": node.id}
                for field_name in import_command["field"]:
                    if field_name == "name":
                        after_entry[field_name] = intf_conv.normalization(
                            interface_info[import_command["field"][field_name]]
                        )
                    else:
                        after_entry[field_name] = interface_info[
                            import_command["field"][field_name]
                        ]
                for field_name in delta_field:
                    if (
                        intf_conv.normalization(
                            interface_info[import_command["field"]["name"]]
                        )
                        in before
                    ):
                        after_entry[field_name] = before[
                            intf_conv.normalization(
                                interface_info[import_command["field"]["name"]]
                            )
                        ][field_name]
                    else:
                        after_entry[field_name] = None

                after[
                    intf_conv.normalization(
                        interface_info[import_command["field"]["name"]]
                    )
                ] = after_entry

            delta_commit(
                model=Interface,
                before_keys=before_interfaces,
                before=before,
                after_keys=after_interfaces,
                after=after,
            )


def import_arp_entry(node):
    intf_conv = IntfAbbrevConverter(node.device_type)
    import_command_mapper = ImportCommandMapper(node.device_type)
    after_arp_entries = set()
    after = dict()
    interfaces = {interface.name: interface.id for interface in node.interfaces}

    for import_command in import_command_mapper.mapping_dict["import_arp_entry"]:
        before_field = {"ip_address", "mac_address", "protocol", "arp_type", "vendor"}
        arp_entries = ArpEntry.query.filter(
            ArpEntry.interface_id.in_(interfaces.values())
        ).all()
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
                    "vendor": arp_entry.vendor,
                }

        result = node.command_with_history(
            import_command["command"], current_user.email
        )
        if isinstance(result, list):
            result = [
                record
                for record in result
                if is_not_ignore_record(record, import_command)
            ]
            after_arp_entries = {
                arp_entry_info[import_command["field"]["ip_address"]]
                for arp_entry_info in result
            }
            after_field = set(import_command["field"])
            delta_field = before_field - after_field
            for arp_entry_info in result:
                if arp_entry_info["interface"] != "":
                    after_entry = {
                        "interface_id": interfaces[
                            intf_conv.normalization(arp_entry_info["interface"])
                        ]
                    }
                    for field_name in import_command["field"]:
                        after_entry[field_name] = arp_entry_info[
                            import_command["field"][field_name]
                        ]
                    for field_name in delta_field:
                        if (
                            arp_entry_info[import_command["field"]["ip_address"]]
                            in before
                        ):
                            after_entry[field_name] = before[
                                arp_entry_info[import_command["field"]["ip_address"]]
                            ][field_name]
                        else:
                            after_entry[field_name] = None

                after[arp_entry_info[import_command["field"]["ip_address"]]] = (
                    after_entry
                )

            delta_commit(
                model=ArpEntry,
                before_keys=before_arp_entries,
                before=before,
                after_keys=after_arp_entries,
                after=after,
            )


def import_target_node(node):
    import_node(node)
    import_serial(node)
    import_interface(node)
    import_arp_entry(node)


def is_not_ignore_record(record, import_command):
    if "ignore" in import_command:
        for ignore in import_command["ignore"]:
            if all(record[key] == value for key, value in ignore.items()):
                logger.debug(f"record is ignored: {record}")
                return False
    return True
