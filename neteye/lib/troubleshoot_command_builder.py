"""troubleshoot_command_builder.py

Device-specific troubleshoot command builders.

Each device type has a corresponding subclass that implements build_ping()
and build_traceroute(). build_telnet() is planned for future releases.

To add support for a new device type:
  1. Create a subclass of TroubleshootBuilder and implement build_ping()
     and build_traceroute().
  2. Add one entry to _BUILDER_REGISTRY.
  3. Add test cases to tests/test_troubleshoot_command_builder.py.
  No changes to callers (routes.py etc.) are required.
"""

from abc import ABC, abstractmethod


class UnsupportedDeviceTypeError(Exception):
    """Raised when no builder is registered for the given device_type."""
    pass


class TroubleshootBuilder(ABC):
    """Abstract base class for device-specific troubleshoot command builders.

    Subclasses must implement build_ping() and build_traceroute().
    build_telnet() raises NotImplementedError until implemented.
    The helper method _optional() is shared across ping, traceroute, and telnet commands.
    """

    @abstractmethod
    def build_ping(
        self,
        dst_ip: str,
        src_ip: str | None,
        vrf: str | None,
        count: int,
        timeout: int,
        size: int,
    ) -> str | list[str]:
        """Return the ping command string, or a list of strings for multi-step devices."""
        ...

    @abstractmethod
    def build_traceroute(
        self,
        dst_ip: str,
        src_ip: str | None,
        vrf: str | None,
        probe: int,
        timeout: int,
        max_ttl: int,
    ) -> str | list[str]:
        """Return the traceroute command string, or a list of strings for multi-step devices.

        Args:
            probe: Number of probes per hop (sent per TTL value).
            max_ttl: Maximum TTL (controls the maximum number of hops).
        """
        ...

    def build_telnet(
        self,
        host: str,
        port: int,
        vrf: str | None,
        src_ip: str | None,
    ) -> str | list[str]:
        raise NotImplementedError(
            f"telnet is not yet implemented for {type(self).__name__}"
        )

    # ── Shared helpers ───────────────────────────────────────────────

    def _optional(self, keyword: str, value: str | None) -> list[str]:
        """Return ['{keyword} {value}'] when value is given, else [].

        Use with += to conditionally append a keyword-value pair to a command list:
            command += self._optional("vrf", vrf)
        """
        return [f"{keyword} {value}"] if value else []



# ── Device-specific builders ─────────────────────────────────────────


class CiscoIOSTroubleshootBuilder(TroubleshootBuilder):
    """Cisco IOS / IOS-XE (shared — identical syntax)."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping [vrf VRF] DST [source SRC] repeat N timeout N size N
        command  = ["ping"]
        command += self._optional("vrf", vrf)
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += [f"repeat {count}"]
        command += [f"timeout {timeout}"]
        command += [f"size {size}"]
        return " ".join(command)

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # traceroute [vrf VRF] DST [source SRC] probe N timeout N ttl 1 N
        command  = ["traceroute"]
        command += self._optional("vrf", vrf)
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += [f"probe {probe}"]
        command += [f"timeout {timeout}"]
        command += [f"ttl 1 {max_ttl}"]
        return " ".join(command)


class CiscoNXOSTroubleshootBuilder(TroubleshootBuilder):
    """Cisco NX-OS."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping DST count N [source SRC] [vrf VRF] packet-size N timeout N
        command  = ["ping"]
        command += [dst_ip]
        command += [f"count {count}"]
        command += self._optional("source", src_ip)
        command += self._optional("vrf", vrf)
        command += [f"packet-size {size}"]
        command += [f"timeout {timeout}"]
        return " ".join(command)

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # traceroute DST [source SRC] [vrf VRF] probe N timeout N
        # NX-OS does not support a max-ttl option (max_ttl is ignored)
        command  = ["traceroute"]
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += self._optional("vrf", vrf)
        command += [f"probe {probe}"]
        command += [f"timeout {timeout}"]
        return " ".join(command)


class CiscoXRTroubleshootBuilder(TroubleshootBuilder):
    """Cisco IOS-XR."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping [vrf VRF] DST [source SRC] count N timeout N size N
        command  = ["ping"]
        command += self._optional("vrf", vrf)
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += [f"count {count}"]
        command += [f"timeout {timeout}"]
        command += [f"size {size}"]
        return " ".join(command)

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # traceroute [vrf VRF] DST [source SRC] probe N timeout N max-ttl N
        command  = ["traceroute"]
        command += self._optional("vrf", vrf)
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += [f"probe {probe}"]
        command += [f"timeout {timeout}"]
        command += [f"max-ttl {max_ttl}"]
        return " ".join(command)


class AristaEOSTroubleshootBuilder(TroubleshootBuilder):
    """Arista EOS."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping DST [source SRC] repeat N size N [vrf VRF]
        command  = ["ping"]
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += [f"repeat {count}"]
        command += [f"size {size}"]
        command += self._optional("vrf", vrf)
        return " ".join(command)

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # traceroute DST [source SRC] probe N maxttl N
        # Arista does not support a timeout option (timeout is ignored)
        command  = ["traceroute"]
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += [f"probe {probe}"]
        command += [f"maxttl {max_ttl}"]
        return " ".join(command)


class JuniperJunOSTroubleshootBuilder(TroubleshootBuilder):
    """Juniper JunOS. VRF keyword is 'routing-instance' (differs from other vendors)."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping DST count N [source SRC] [routing-instance VRF] size N wait N
        command  = ["ping"]
        command += [dst_ip]
        command += [f"count {count}"]
        command += self._optional("source", src_ip)
        command += self._optional("routing-instance", vrf)
        command += [f"size {size}"]
        command += [f"wait {timeout}"]
        return " ".join(command)

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # traceroute DST [source SRC] [routing-instance VRF] probe-count N wait N ttl N
        command  = ["traceroute"]
        command += [dst_ip]
        command += self._optional("source", src_ip)
        command += self._optional("routing-instance", vrf)
        command += [f"probe-count {probe}"]
        command += [f"wait {timeout}"]
        command += [f"ttl {max_ttl}"]
        return " ".join(command)


class PaloAltoTroubleshootBuilder(TroubleshootBuilder):
    """Palo Alto PAN-OS. VRF equivalent is 'vrouter'."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping [vrouter VRF] host DST [source SRC] count N
        command  = ["ping"]
        command += self._optional("vrouter", vrf)
        command += ["host", dst_ip]
        command += self._optional("source", src_ip)
        command += [f"count {count}"]
        return " ".join(command)

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # traceroute host DST [source SRC]
        # vrouter/probe/timeout/max_ttl are not supported for traceroute on PAN-OS
        command  = ["traceroute", "host"]
        command += [dst_ip]
        command += self._optional("source", src_ip)
        return " ".join(command)


class CiscoASATroubleshootBuilder(TroubleshootBuilder):
    """Cisco ASA. VRF and source IP are not supported (context-dependent architecture)."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping <dst>
        return f"ping {dst_ip}"

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # traceroute DST (src/vrf/probe/timeout/ttl not supported)
        return f"traceroute {dst_ip}"


class FortinetTroubleshootBuilder(TroubleshootBuilder):
    """Fortinet FortiOS. Returns a list of commands (multi-step) for ping. VRF not supported."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> list[str]:
        # Configure options with 'execute ping-options', then run 'execute ping'
        commands: list[str] = []
        if src_ip:
            commands.append(f"execute ping-options source {src_ip}")
        commands.append(f"execute ping-options count {count}")
        commands.append(f"execute ping-options timeout {timeout}")
        commands.append(f"execute ping-options data-size {size}")
        commands.append(f"execute ping {dst_ip}")
        return commands

    def build_traceroute(self, dst_ip, src_ip, vrf, probe, timeout, max_ttl) -> str:
        # execute traceroute DST (single command; src/vrf/probe/timeout not supported)
        return f"execute traceroute {dst_ip}"


# ── Factory ──────────────────────────────────────────────────────────
# To add a new device type: add one entry here + one class above.
# Callers do not need to change.

_BUILDER_REGISTRY: dict[str, TroubleshootBuilder] = {
    "cisco_ios":      CiscoIOSTroubleshootBuilder(),
    "cisco_xe":       CiscoIOSTroubleshootBuilder(),    # identical syntax
    "cisco_nxos":     CiscoNXOSTroubleshootBuilder(),
    "cisco_xr":       CiscoXRTroubleshootBuilder(),
    "arista_eos":     AristaEOSTroubleshootBuilder(),
    "juniper_junos":  JuniperJunOSTroubleshootBuilder(),
    "paloalto_panos": PaloAltoTroubleshootBuilder(),
    "cisco_asa":      CiscoASATroubleshootBuilder(),    # source/VRF not supported
    "fortinet":       FortinetTroubleshootBuilder(),    # returns list[str]
}


def get_troubleshoot_builder(device_type: str) -> TroubleshootBuilder:
    """Return the builder for the given device_type.

    Raises UnsupportedDeviceTypeError if no builder is registered.
    """
    builder = _BUILDER_REGISTRY.get(device_type)
    if builder is None:
        raise UnsupportedDeviceTypeError(device_type)
    return builder


# ── Ping interrupt sequences ──────────────────────────────────────────
# Sent to the device when the user cancels a running ping.

_INTERRUPT_CHARS: dict[str, str] = {
    "cisco_ios":      "\x1e",   # Ctrl+Shift+6 — Cisco standard ping interrupt
    "cisco_xe":       "\x1e",
    "cisco_nxos":     "\x1e",
    "cisco_xr":       "\x1e",
    "cisco_asa":      "\x1e",
    "arista_eos":     "\x03",   # Ctrl+C
    "juniper_junos":  "\x03",
    "paloalto_panos": "\x03",
    "fortinet":       "\x03",
}


def get_interrupt_char(device_type: str) -> str:
    """Return the character sequence that interrupts a running command for the given device_type.

    Used to abort long-running commands (ping, traceroute, etc.) mid-execution.
    Falls back to Ctrl+C (\\x03) for unknown device types.
    """
    return _INTERRUPT_CHARS.get(device_type, "\x03")
