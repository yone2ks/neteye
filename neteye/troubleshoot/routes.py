import logging
import time

from flask import Response, flash, render_template, request, stream_with_context
from flask_security import auth_required, current_user

from neteye.blueprints import bp_factory
from neteye.extensions import settings
from neteye.history.model_command_history import CommandHistory
from neteye.interface.models import Interface
from neteye.lib.troubleshoot_command_builder import (
    UnsupportedDeviceTypeError,
    get_interrupt_char,
    get_troubleshoot_builder,
)
from neteye.lib.utils.report_exception import report_exception
from neteye.node.models import Node

from .forms import PingForm

logger = logging.getLogger(__name__)

troubleshoot_bp = bp_factory("troubleshoot")


def _annotate_ip(ip_address: str) -> str | None:
    """Look up an IP address in the Node and Interface tables and return an annotation string.

    Returns None when the address is not found.
    Will be extracted into ip_annotator.py when traceroute is implemented.
    """
    node = Node.query.filter_by(ip_address=ip_address).first()
    if node:
        return node.hostname

    iface = Interface.query.filter_by(ip_address=ip_address).first()
    if iface:
        return f"{iface.node.hostname} ({iface.name})"

    return None


@troubleshoot_bp.route("/ping")
@auth_required()
def ping():
    form = PingForm()
    return render_template("/troubleshoot/ping.html", form=form)


@troubleshoot_bp.route("/ping", methods=["POST"])
@auth_required()
def ping_execute():
    form = PingForm()

    # Rebuild src_ip_address choices from the DB before validation.
    # The choices are populated client-side via AJAX, so the server-side form
    # object has an empty list by default, which would cause validation to fail.
    if form.src_node.data:
        interfaces = Interface.query.filter_by(
            node_id=form.src_node.data.id
        ).all()
        form.src_ip_address.choices = [
            (iface.ip_address, iface.ip_address)
            for iface in interfaces
            if iface.ip_address and iface.ip_address != "unassigned"
        ]

    if not form.validate_on_submit():
        return render_template("/troubleshoot/ping.html", form=form)

    node = form.src_node.data
    dst_ip = form.dst_ip_address.data
    src_ip = form.src_ip_address.data or None
    vrf = form.vrf.data or None
    count = form.count.data
    timeout = form.timeout.data
    size = form.data_size.data

    # Build the device-specific ping command.
    try:
        builder = get_troubleshoot_builder(node.device_type)
        command = builder.build_ping(
            dst_ip=dst_ip,
            src_ip=src_ip,
            vrf=vrf,
            count=count,
            timeout=timeout,
            size=size,
        )
    except UnsupportedDeviceTypeError:
        flash(
            f"Ping is not supported for device type: {node.device_type}",
            "warning",
        )
        return render_template("/troubleshoot/ping.html", form=form)

    # Execute the command. Set read_timeout based on expected ping duration.
    # Use netmiko_raw_command directly: scrapli's timeout_transport is fixed at
    # connection creation and cannot be overridden per-command, causing EOF errors
    # on long-running commands. netmiko's read_timeout works correctly per-command.
    read_timeout = count * timeout + 10
    try:
        if isinstance(command, list):
            # Multi-step command (e.g. Fortinet): run each step and join the output.
            outputs = [
                node.netmiko_raw_command(cmd, current_user.email, timeout=read_timeout)
                for cmd in command
            ]
            result = "\n".join(filter(None, outputs))
            command_str = "\n".join(command)
        else:
            result = node.netmiko_raw_command(command, current_user.email, timeout=read_timeout)
            command_str = command
    except Exception as err:
        report_exception(err, "Ping execution failed")
        return render_template("/troubleshoot/ping.html", form=form)

    # Annotate the destination IP with a hostname/interface name from the DB if available.
    dst_annotation = _annotate_ip(dst_ip)

    return render_template(
        "/troubleshoot/ping.html",
        form=form,
        result=result,
        command=command_str,
        dst_ip=dst_ip,
        dst_annotation=dst_annotation,
    )


@troubleshoot_bp.route("/ping/stream")
@auth_required()
def ping_stream():
    """Server-Sent Events endpoint for real-time ping output.

    Accepts GET parameters: node_id, dst_ip, src_ip, vrf, count, timeout, size.
    Uses a dedicated netmiko connection (not from the connection pool) so that
    write_channel/read_channel can be used without interfering with pooled connections.
    """
    node_id = request.args.get("node_id", "").strip()
    dst_ip = request.args.get("dst_ip", "").strip()
    src_ip = request.args.get("src_ip", "").strip() or None
    vrf = request.args.get("vrf", "").strip() or None
    count = min(max(request.args.get("count", 5, type=int), 1), settings.PING_MAX_COUNT)
    timeout = min(max(request.args.get("timeout", 2, type=int), 1), settings.PING_MAX_TIMEOUT)
    size = request.args.get("size", 100, type=int)

    node = Node.query.filter_by(id=node_id).first() if node_id else None

    def generate():
        # --- Validation ---
        if not node:
            yield "data: ERROR: Node not found\n\n"
            yield "data: [DONE]\n\n"
            return
        if not dst_ip:
            yield "data: ERROR: Destination IP is required\n\n"
            yield "data: [DONE]\n\n"
            return

        # --- Build command ---
        try:
            builder = get_troubleshoot_builder(node.device_type)
            command = builder.build_ping(
                dst_ip=dst_ip,
                src_ip=src_ip,
                vrf=vrf,
                count=count,
                timeout=timeout,
                size=size,
            )
        except UnsupportedDeviceTypeError:
            yield f"data: ERROR: Ping is not supported for device type: {node.device_type}\n\n"
            yield "data: [DONE]\n\n"
            return

        commands = command if isinstance(command, list) else [command]
        command_str = "\n".join(commands) if isinstance(command, list) else command

        # --- Emit header info ---
        dst_annotation = _annotate_ip(dst_ip)
        annotation_suffix = f" -> {dst_annotation}" if dst_annotation else ""
        yield f"data: Destination : {dst_ip}{annotation_suffix}\n\n"
        yield f"data: Command     : {command_str}\n\n"
        yield "data: \n\n"

        # --- Open dedicated connection (not from pool) ---
        try:
            conn = node.gen_netmiko_connection()
        except Exception as err:
            report_exception(err, "Ping connection failed")
            yield f"data: ERROR: Connection failed: {err}\n\n"
            yield "data: [DONE]\n\n"
            return

        # --- Stream output ---
        try:
            prompt = conn.find_prompt()
            deadline = time.time() + count * timeout + 30

            for cmd in commands:
                conn.write_channel(cmd + "\n")
                time.sleep(0.2)

                buffer = ""
                while time.time() < deadline:
                    chunk = conn.read_channel()
                    if chunk:
                        buffer += chunk
                        for line in chunk.splitlines():
                            if line.strip():
                                yield f"data: {line}\n\n"
                        if prompt in buffer:
                            break
                    else:
                        time.sleep(0.3)

            # --- Record to CommandHistory (normal completion only) ---
            try:
                CommandHistory(
                    username=current_user.email,
                    node_id=node.id,
                    hostname=node.hostname,
                    command=command_str,
                    result="(streamed via SSE)",
                ).add()
            except Exception as err:
                logger.warning("Failed to record ping to history: %s", err)

        except GeneratorExit:
            # Client cancelled the stream — send device-specific interrupt to stop the ping.
            interrupt_char = get_interrupt_char(node.device_type)
            try:
                conn.write_channel(interrupt_char)
                time.sleep(0.2)
            except Exception:
                pass
            raise   # Re-raise so the generator exits cleanly.

        except Exception as err:
            report_exception(err, "Ping execution failed")
            yield f"data: ERROR: {err}\n\n"
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass

        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
