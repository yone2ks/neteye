"""troubleshoot_command_builder.py

Device-specific troubleshoot command builders.

Each device type has a corresponding subclass that implements build_ping().
build_traceroute() and build_telnet() are planned for future releases.

To add support for a new device type:
  1. Create a subclass of TroubleshootBuilder and implement build_ping().
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

    Subclasses must implement build_ping().
    build_traceroute() and build_telnet() raise NotImplementedError until implemented.
    The helper methods _vrf_part() and _src_part() are shared across ping, traceroute,
    and telnet commands.
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

    def build_traceroute(
        self,
        dst_ip: str,
        src_ip: str | None,
        vrf: str | None,
        count: int,
        timeout: int,
        size: int,
    ) -> str | list[str]:
        raise NotImplementedError(
            f"traceroute is not yet implemented for {type(self).__name__}"
        )

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

    def _vrf_part(self, keyword: str, vrf: str | None) -> str:
        """Return 'keyword vrf ' (trailing space) when vrf is given, else empty string."""
        return f"{keyword} {vrf} " if vrf else ""

    def _src_part(self, keyword: str, src_ip: str | None) -> str:
        """Return ' keyword src_ip' (leading space) when src_ip is given, else empty string."""
        return f" {keyword} {src_ip}" if src_ip else ""


# ── Device-specific builders ─────────────────────────────────────────


class CiscoIOSTroubleshootBuilder(TroubleshootBuilder):
    """Cisco IOS / IOS-XE (shared — identical syntax)."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping [vrf <vrf>] <dst> [source <src>] [repeat <n>] [timeout <n>] [size <n>]
        vrf_part = self._vrf_part("vrf", vrf)
        src_part = self._src_part("source", src_ip)
        return (
            f"ping {vrf_part}{dst_ip}{src_part}"
            f" repeat {count} timeout {timeout} size {size}"
        )


class CiscoNXOSTroubleshootBuilder(TroubleshootBuilder):
    """Cisco NX-OS."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping <dst> [count <n>] [source <src>] [vrf <vrf>] [packet-size <n>] [timeout <n>]
        parts = [f"ping {dst_ip}", f"count {count}"]
        if src_ip:
            parts.append(f"source {src_ip}")
        if vrf:
            parts.append(f"vrf {vrf}")
        parts.append(f"packet-size {size}")
        parts.append(f"timeout {timeout}")
        return " ".join(parts)


class CiscoXRTroubleshootBuilder(TroubleshootBuilder):
    """Cisco IOS-XR."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping [vrf <vrf>] <dst> [source <src>] [count <n>] [timeout <n>] [size <n>]
        vrf_part = self._vrf_part("vrf", vrf)
        src_part = self._src_part("source", src_ip)
        return (
            f"ping {vrf_part}{dst_ip}{src_part}"
            f" count {count} timeout {timeout} size {size}"
        )


class AristaEOSTroubleshootBuilder(TroubleshootBuilder):
    """Arista EOS."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping <dst> [source <src>] [repeat <n>] [size <n>] [vrf <vrf>]
        parts = [f"ping {dst_ip}"]
        if src_ip:
            parts.append(f"source {src_ip}")
        parts.append(f"repeat {count}")
        parts.append(f"size {size}")
        if vrf:
            parts.append(f"vrf {vrf}")
        return " ".join(parts)


class JuniperJunOSTroubleshootBuilder(TroubleshootBuilder):
    """Juniper JunOS. VRF keyword is 'routing-instance' (differs from other vendors)."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping <dst> [count <n>] [source <src>] [routing-instance <vrf>] [size <n>] [wait <n>]
        src_part = self._src_part("source", src_ip)
        ri_part = self._vrf_part("routing-instance", vrf)
        return (
            f"ping {dst_ip} count {count}{src_part}"
            f" {ri_part}size {size} wait {timeout}"
        ).strip()


class PaloAltoTroubleshootBuilder(TroubleshootBuilder):
    """Palo Alto PAN-OS. VRF equivalent is 'vrouter'."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping [vrouter <vrf>] host <dst> [source <src>] [count <n>]
        parts = ["ping"]
        if vrf:
            parts.append(f"vrouter {vrf}")
        parts.append(f"host {dst_ip}")
        if src_ip:
            parts.append(f"source {src_ip}")
        parts.append(f"count {count}")
        return " ".join(parts)


class CiscoASATroubleshootBuilder(TroubleshootBuilder):
    """Cisco ASA. VRF and source IP are not supported (context-dependent architecture)."""

    def build_ping(self, dst_ip, src_ip, vrf, count, timeout, size) -> str:
        # ping <dst>
        return f"ping {dst_ip}"


class FortinetTroubleshootBuilder(TroubleshootBuilder):
    """Fortinet FortiOS. Returns a list of commands (multi-step). VRF not supported."""

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
