from logging import debug, error, getLogger, info

import netmiko
import pandas as pd
import sqlalchemy
from datatables import ColumnDT, DataTables
from flask import flash, jsonify, redirect, render_template, request, session, url_for
from flask_security import auth_required, current_user
from netaddr import *
from neteye.base.models import gen_uuid_str
from neteye.arp_entry.models import ArpEntry
from neteye.blueprints import bp_factory, root_bp
from neteye.extensions import connection_pool, db, ntc_template_utils, settings
from neteye.interface.models import Interface
from neteye.lib.import_command_mapper.import_command_mapper import ImportCommandMapper, IMPORT_TYPES
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from neteye.lib.utils.neteye_differ import delta_commit
from neteye.lib.utils.neteye_normalizer import normalize_noop, normalize_mac_address, normalize_mask, normalize_speed, normalize_duplex
from neteye.lib.utils.get_records_by_node import get_records_dict_by_node
from neteye.serial.models import Serial
from sqlalchemy.sql import exists

from .forms import NodeForm
from .models import NAPALM_DRIVERS, NETMIKO_PLATFORMS, SCRAPLI_DRIVERS, Node

logger = getLogger(__name__)

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
    command_list = ntc_template_utils.get_command_list(node.ntc_template_platform)
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
#    try:
        node = Node.query.get(id)
        import_target_node(node)
        logger.info(f"Node {id} imported successfully")
        return redirect(url_for("node.show", id=id))
#    except Exception as err:
#        logger.error(f"Error importing node {id}: {type(err).__name__}, {str(err)}")
#        return redirect(url_for("node.show", id=id))


@node_bp.route("/import_node_from_ip/<ip_address>")
@auth_required()
def import_node_from_ip(ip_address):
    try:
        node = try_connect_node(ip_address)
        if node:
            import_target_node(node)
            logger.info(f"Node {ip_address} imported successfully")
            return redirect(url_for("node.index"))
    except Exception as err:
        logger.error(f"Error importing node {ip_address}: {type(err).__name__}, {str(err)}")
        return redirect(url_for("node.show", id=node.id))


@node_bp.route("/import_interface/<id>")
@auth_required()
def import_interface_only(id):
    """Import interface data for a specific node"""
    try:
        node = Node.query.get(id)
        if not node:
            flash(f"Node with ID {id} not found", "error")
            return redirect(url_for("node.index"))
        
        import_interface(node)
        flash(f"Interface data imported successfully for node {node.hostname}", "success")
        logger.info(f"Interface data imported for node {id}")
        return redirect(url_for("node.show", id=id))
    except Exception as err:
        logger.error(f"Error importing interface data for node {id}: {type(err).__name__}, {str(err)}")
        flash(f"Error importing interface data: {str(err)}", "error")
        return redirect(url_for("node.show", id=id))


@node_bp.route("/import_serial/<id>")
@auth_required()
def import_serial_only(id):
    """Import serial data for a specific node"""
    try:
        node = Node.query.get(id)
        if not node:
            flash(f"Node with ID {id} not found", "error")
            return redirect(url_for("node.index"))
        
        import_serial(node)
        flash(f"Serial data imported successfully for node {node.hostname}", "success")
        logger.info(f"Serial data imported for node {id}")
        return redirect(url_for("node.show", id=id))
    except Exception as err:
        logger.error(f"Error importing serial data for node {id}: {type(err).__name__}, {str(err)}")
        flash(f"Error importing serial data: {str(err)}", "error")
        return redirect(url_for("node.show", id=id))


@node_bp.route("/import_arp/<id>")
@auth_required()
def import_arp_only(id):
    """Import ARP entry data for a specific node"""
    try:
        node = Node.query.get(id)
        if not node:
            flash(f"Node with ID {id} not found", "error")
            return redirect(url_for("node.index"))
        
        import_arp_entry(node)
        flash(f"ARP entry data imported successfully for node {node.hostname}", "success")
        logger.info(f"ARP entry data imported for node {id}")
        return redirect(url_for("node.show", id=id))
    except Exception as err:
        logger.error(f"Error importing ARP entry data for node {id}: {type(err).__name__}, {str(err)}")
        flash(f"Error importing ARP entry data: {str(err)}", "error")
        return redirect(url_for("node.show", id=id))


@node_bp.route("/import_node/<id>")
@auth_required()
def import_node_only(id):
    """Import node data for a specific node"""
    try:
        node = Node.query.get(id)
        if not node:
            flash(f"Node with ID {id} not found", "error")
            return redirect(url_for("node.index"))
        
        import_node(node)
        flash(f"Node data imported successfully for node {node.hostname}", "success")
        logger.info(f"Node data imported for node {id}")
        return redirect(url_for("node.show", id=id))
    except Exception as err:
        logger.error(f"Error importing node data for node {id}: {type(err).__name__}, {str(err)}")
        flash(f"Error importing node data: {str(err)}", "error")
        return redirect(url_for("node.show", id=id))


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
        if Interface.query.filter_by(ip_address=entry.ip_address).first() is None:
            try:
                target_node = try_connect_node(entry.ip_address)
                if target_node:
                    import_target_node(target_node)
            except Exception as err:
                break


def try_connect_node(ip_address):
    for cred in settings.credentials.values():
        try:
            logger.debug(f"Trying to connect to {ip_address}")
            id = gen_uuid_str()
            node = Node(
                id=id,
                hostname=id,
                ip_address=ip_address,
                port=22,
                device_type="autodetect",
                username=cred["USERNAME"],
                password=cred["PASSWORD"],
                enable=cred["ENABLE"],
            )
            node.raw_command('\n')
            node.add()
            logger.info(f"Successfully connected to {ip_address}")
            return node
        except (
            netmiko.exceptions.NetMikoTimeoutException,
            netmiko.exceptions.SSHException,
            ValueError,
        ) as err:
            logger.error(f"Error connecting to {ip_address}: {type(err).__name__}, {str(err)}")
            continue
        except Exception as err:
            logger.error(f"Error connecting to {ip_address}: {type(err).__name__}, {str(err)}")
            break
    return False


def import_common(node, model):
    """
    Generic import function to retrieve data from a device (node) 
    and update the database model accordingly.

    Args:
        node: The target node from which data is retrieved.
        model: The SQLAlchemy model where the data will be stored.
    """
    import_command_mapper = ImportCommandMapper(node.device_type)
    import_type = IMPORT_TYPES[model]
    key_field = model.KEY # Unique key field (e.g., serial number, IP address, etc.)
    
    # get data for each command and commit the changes to the database
    for command in import_command_mapper.get_commands(import_type):
        # get current records information
        before_records = { record[key_field]: record for record in get_records_dict_by_node(model, node.id) }
        before_keys = set(before_records.keys())
        before_field = model.ATTRIBUTES
        after_records = {}
        
        # execute import command and get result
        result = node.command_with_history(command, current_user.email)
        
        if isinstance(result, list):
            index = import_command_mapper.get_index(import_type, command)
            filtered_result = import_command_mapper.filter_ignore_records(import_type=import_type, command=command, result=result)
            # get the fields in command result
            after_field = set(import_command_mapper.get_fields(import_type, command).keys())
            # get delta between before_field and after_field. delta_fields is not included in the result, so assign a before value in the fields.
            delta_field = (before_field - after_field) - {"node_id"}
            
            # If an index is specified, only the record information of the corresponding index is processed. Otherwise, all records are processed.
            for record in (filtered_result if index is None else [filtered_result[index]]):
                record_key = import_command_mapper.get_value_from_record(import_type=import_type, command=command, field=key_field, record=record)
                after_entry = {"node_id": node.id} if "node_id" in before_field else {}
                # process for each field in the command result
                for field_name in import_command_mapper.get_fields(import_type, command):
                    after_entry[field_name] = import_command_mapper.get_value_from_record(import_type=import_type, command=command, field=field_name, record=record)
                # process for non-existent fields in the command result
                for field_name in delta_field:
                    after_entry[field_name] = before_records.get(record_key, {}).get(field_name)

                after_records[record_key] = after_entry

            # commit the changes to the database for the command
            delta_commit(model=model, before_keys=before_keys, before=before_records, after_keys=set(after_records.keys()), after=after_records)


def import_serial(node):
    import_common(node, Serial)


def import_node(node):
    import_command_mapper = ImportCommandMapper(node.device_type)
    import_type = IMPORT_TYPES[Node]
    
    for command in import_command_mapper.get_commands(import_type):
        result = node.command_with_history(command, current_user.email)
        if isinstance(result, list):
            index = import_command_mapper.get_index(import_type, command)
            fields = import_command_mapper.get_fields(import_type, command)
            
            for record in (result if index is None else [result[index]]):
                for field_name in fields.keys():
                    setattr(node, field_name, import_command_mapper.get_value_from_record(import_type, command, field_name, record))
    node.commit()


def import_interface(node):
    import_common(node, Interface)

def import_arp_entry(node):
    import_common(node, ArpEntry)

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
