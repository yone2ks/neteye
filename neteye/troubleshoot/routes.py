import json
import logging
import re
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

from .forms import (
    PING_DEFAULT_COUNT,
    PING_DEFAULT_DATA_SIZE,
    PING_DEFAULT_TIMEOUT,
    TRACEROUTE_DEFAULT_MAX_TTL,
    TRACEROUTE_DEFAULT_PROBE,
    TRACEROUTE_DEFAULT_TIMEOUT,
    TRACEROUTE_MAX_PROBE,
    PingForm,
    TracerouteForm,
)

logger = logging.getLogger(__name__)

troubleshoot_bp = bp_factory("troubleshoot")


# ── SSE helpers — shared by all streaming routes ──────────────────────

def _sse_message(text: str) -> str:
    """Format text as a single SSE data line (data: <text>\\n\\n)."""
    return f"data: {text}\n\n"


_SSE_DONE      = _sse_message("[DONE]")
_SSE_SEPARATOR = _sse_message("")   # blank line between header info and streaming output


# ── Annotation helpers ────────────────────────────────────────────────

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


_IP_RE = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b')


def _annotate_traceroute_line(line: str) -> str:
    """Annotate IPv4 addresses in a traceroute hop line with Node/Interface DB lookups.

    Each IPv4 address found in the line is looked up via _annotate_ip().
    If a match is found, the annotation is appended in brackets:
      192.168.1.1  ->  192.168.1.1 [router1 (Gi0/0)]
    """
    def _replace(match: re.Match) -> str:
        ip = match.group(1)
        annotation = _annotate_ip(ip)
        return f"{ip} [{annotation}]" if annotation else ip
    return _IP_RE.sub(_replace, line)


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
    commands = command if isinstance(command, list) else [command]
    commands_str = "\n".join(commands)
    read_timeout = count * timeout + 10
    try:
        outputs = [
            node.netmiko_raw_command(step, current_user.email, timeout=read_timeout)
            for step in commands
        ]
        result = "\n".join(filter(None, outputs))
    except Exception as err:
        report_exception(err, "Ping execution failed")
        return render_template("/troubleshoot/ping.html", form=form)

    # Annotate the destination IP with a hostname/interface name from the DB if available.
    dst_annotation = _annotate_ip(dst_ip)

    return render_template(
        "/troubleshoot/ping.html",
        form=form,
        result=result,
        command=commands_str,
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
    count = min(max(request.args.get("count", PING_DEFAULT_COUNT, type=int), 1), settings.PING_MAX_COUNT)
    timeout = min(max(request.args.get("timeout", PING_DEFAULT_TIMEOUT, type=int), 1), settings.PING_MAX_TIMEOUT)
    size = request.args.get("size", PING_DEFAULT_DATA_SIZE, type=int)

    node = Node.query.filter_by(id=node_id).first() if node_id else None

    def generate():
        # --- Validation ---
        if not node:
            yield _sse_message("ERROR: Node not found")
            yield _SSE_DONE
            return
        if not dst_ip:
            yield _sse_message("ERROR: Destination IP is required")
            yield _SSE_DONE
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
            yield _sse_message(f"ERROR: Ping is not supported for device type: {node.device_type}")
            yield _SSE_DONE
            return

        commands = command if isinstance(command, list) else [command]
        commands_str = "\n".join(commands)

        # --- Emit header info ---
        dst_annotation = _annotate_ip(dst_ip)
        annotation_suffix = f" -> {dst_annotation}" if dst_annotation else ""
        yield _sse_message(f"Destination : {dst_ip}{annotation_suffix}")
        yield _sse_message(f"Command     : {commands_str}")
        yield _SSE_SEPARATOR

        # --- Open dedicated connection (not from pool) ---
        try:
            conn = node.gen_netmiko_connection()
        except Exception as err:
            report_exception(err, "Ping connection failed")
            yield _sse_message(f"ERROR: Connection failed: {err}")
            yield _SSE_DONE
            return

        # --- Stream output ---
        output_lines: list[str] = []
        try:
            prompt = conn.find_prompt()
            deadline = time.time() + count * timeout + 30

            for command in commands:
                conn.write_channel(command + "\n")
                time.sleep(0.2)

                buffer = ""
                while time.time() < deadline:
                    chunk = conn.read_channel()
                    if chunk:
                        buffer += chunk
                        for line in chunk.splitlines():
                            if line.strip():
                                output_lines.append(line)
                                yield _sse_message(line)
                        if prompt in buffer:
                            break
                    else:
                        time.sleep(0.3)

            history_result = "\n".join(output_lines)

        except GeneratorExit:
            # Client cancelled the stream — send device-specific interrupt to stop the ping.
            history_result = "\n".join(output_lines) + "\n(cancelled)"
            interrupt_char = get_interrupt_char(node.device_type)
            try:
                conn.write_channel(interrupt_char)
                time.sleep(0.2)
            except Exception:
                pass
            raise   # Re-raise so the generator exits cleanly.

        except Exception as err:
            history_result = "\n".join(output_lines) + "\n(error)"
            report_exception(err, "Ping execution failed")
            yield _sse_message(f"ERROR: {err}")

        finally:
            # --- Record to CommandHistory (always — including cancel and error) ---
            try:
                CommandHistory(
                    username=current_user.email,
                    node_id=node.id,
                    hostname=node.hostname,
                    command=commands_str,
                    result=json.dumps(history_result),
                ).add()
            except Exception as err:
                logger.warning("Failed to record ping to history: %s", err)
            try:
                conn.disconnect()
            except Exception:
                pass

        yield _SSE_DONE

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@troubleshoot_bp.route("/traceroute")
@auth_required()
def traceroute():
    form = TracerouteForm()
    return render_template("/troubleshoot/traceroute.html", form=form)


@troubleshoot_bp.route("/traceroute/stream")
@auth_required()
def traceroute_stream():
    """SSE endpoint for real-time traceroute output."""
    node_id = request.args.get("node_id", "").strip()
    dst_ip  = request.args.get("dst_ip", "").strip()
    src_ip  = request.args.get("src_ip", "").strip() or None
    vrf     = request.args.get("vrf", "").strip() or None
    max_ttl = min(max(request.args.get("max_ttl", TRACEROUTE_DEFAULT_MAX_TTL, type=int), 1), settings.TRACEROUTE_MAX_TTL)
    probe   = min(max(request.args.get("probe",   TRACEROUTE_DEFAULT_PROBE,   type=int), 1), TRACEROUTE_MAX_PROBE)
    timeout = min(max(request.args.get("timeout", TRACEROUTE_DEFAULT_TIMEOUT, type=int), 1), settings.TRACEROUTE_MAX_TIMEOUT)

    node = Node.query.filter_by(id=node_id).first() if node_id else None

    def generate():
        # --- Validation ---
        if not node:
            yield _sse_message("ERROR: Node not found")
            yield _SSE_DONE
            return
        if not dst_ip:
            yield _sse_message("ERROR: Destination IP is required")
            yield _SSE_DONE
            return

        # --- Build command ---
        try:
            builder = get_troubleshoot_builder(node.device_type)
            command = builder.build_traceroute(
                dst_ip=dst_ip,
                src_ip=src_ip,
                vrf=vrf,
                probe=probe,
                timeout=timeout,
                max_ttl=max_ttl,
            )
        except (UnsupportedDeviceTypeError, NotImplementedError):
            yield _sse_message(f"ERROR: Traceroute is not supported for device type: {node.device_type}")
            yield _SSE_DONE
            return

        commands = command if isinstance(command, list) else [command]
        commands_str = "\n".join(commands)

        # --- Emit header info ---
        dst_annotation = _annotate_ip(dst_ip)
        annotation_suffix = f" -> {dst_annotation}" if dst_annotation else ""
        yield _sse_message(f"Destination : {dst_ip}{annotation_suffix}")
        yield _sse_message(f"Command     : {commands_str}")
        yield _SSE_SEPARATOR

        # --- Open dedicated connection ---
        try:
            conn = node.gen_netmiko_connection()
        except Exception as err:
            report_exception(err, "Traceroute connection failed")
            yield _sse_message(f"ERROR: Connection failed: {err}")
            yield _SSE_DONE
            return

        # --- Stream output ---
        output_lines: list[str] = []
        try:
            prompt = conn.find_prompt()
            # Traceroute can take up to max_ttl * timeout seconds
            deadline = time.time() + max_ttl * timeout + 60

            for command in commands:
                conn.write_channel(command + "\n")
                time.sleep(0.2)

                buffer = ""
                while time.time() < deadline:
                    chunk = conn.read_channel()
                    if chunk:
                        buffer += chunk
                        for line in chunk.splitlines():
                            if line.strip():
                                output_lines.append(line)
                                yield _sse_message(_annotate_traceroute_line(line))
                        if prompt in buffer:
                            break
                    else:
                        time.sleep(0.3)

            history_result = "\n".join(output_lines)

        except GeneratorExit:
            history_result = "\n".join(output_lines) + "\n(cancelled)"
            interrupt_char = get_interrupt_char(node.device_type)
            try:
                conn.write_channel(interrupt_char)
                time.sleep(0.2)
            except Exception:
                pass
            raise

        except Exception as err:
            history_result = "\n".join(output_lines) + "\n(error)"
            report_exception(err, "Traceroute execution failed")
            yield _sse_message(f"ERROR: {err}")

        finally:
            # --- Record to CommandHistory (always — including cancel and error) ---
            try:
                CommandHistory(
                    username=current_user.email,
                    node_id=node.id,
                    hostname=node.hostname,
                    command=commands_str,
                    result=json.dumps(history_result),
                ).add()
            except Exception as err:
                logger.warning("Failed to record traceroute to history: %s", err)
            try:
                conn.disconnect()
            except Exception:
                pass

        yield _SSE_DONE

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
