"""tests/test_troubleshoot_command_builder.py

Unit tests for TroubleshootBuilder device-specific subclasses.
No SSH connection required — these tests only verify command string generation.
"""

import pytest

from neteye.lib.troubleshoot_command_builder import (
    AristaEOSTroubleshootBuilder,
    CiscoASATroubleshootBuilder,
    CiscoIOSTroubleshootBuilder,
    CiscoNXOSTroubleshootBuilder,
    CiscoXRTroubleshootBuilder,
    FortinetTroubleshootBuilder,
    JuniperJunOSTroubleshootBuilder,
    PaloAltoTroubleshootBuilder,
    UnsupportedDeviceTypeError,
    get_troubleshoot_builder,
)


# ── 共通フィクスチャ ─────────────────────────────────────────────────

DST     = "10.0.0.1"
SRC     = "192.168.1.1"
VRF     = "MGMT"
COUNT   = 5
TIMEOUT = 2
SIZE    = 100
MAX_TTL = 30
PROBE   = 3


# ── get_troubleshoot_builder ─────────────────────────────────────────

class TestGetTroubleshootBuilder:
    def test_known_device_type_returns_builder(self):
        builder = get_troubleshoot_builder("cisco_ios")
        assert isinstance(builder, CiscoIOSTroubleshootBuilder)

    def test_cisco_xe_shares_ios_builder(self):
        assert type(get_troubleshoot_builder("cisco_xe")) is type(
            get_troubleshoot_builder("cisco_ios")
        )

    def test_unknown_device_type_raises(self):
        with pytest.raises(UnsupportedDeviceTypeError):
            get_troubleshoot_builder("unknown_vendor")


# ── Cisco IOS / IOS-XE ───────────────────────────────────────────────

class TestCiscoIOSTroubleshootBuilder:
    builder = CiscoIOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert command == "ping vrf MGMT 10.0.0.1 source 192.168.1.1 repeat 5 timeout 2 size 100"

    def test_no_vrf(self):
        command = self.builder.build_ping(DST, SRC, None, COUNT, TIMEOUT, SIZE)
        assert "vrf" not in command
        assert command.startswith("ping 10.0.0.1")

    def test_no_src_ip(self):
        command = self.builder.build_ping(DST, None, VRF, COUNT, TIMEOUT, SIZE)
        assert "source" not in command

    def test_minimal(self):
        command = self.builder.build_ping(DST, None, None, COUNT, TIMEOUT, SIZE)
        assert command == "ping 10.0.0.1 repeat 5 timeout 2 size 100"

    def test_returns_str(self):
        assert isinstance(self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE), str)


# ── Cisco NX-OS ──────────────────────────────────────────────────────

class TestCiscoNXOSTroubleshootBuilder:
    builder = CiscoNXOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert "ping 10.0.0.1" in command
        assert "count 5" in command
        assert "source 192.168.1.1" in command
        assert "vrf MGMT" in command
        assert "packet-size 100" in command
        assert "timeout 2" in command

    def test_no_vrf(self):
        command = self.builder.build_ping(DST, SRC, None, COUNT, TIMEOUT, SIZE)
        assert "vrf" not in command

    def test_no_src_ip(self):
        command = self.builder.build_ping(DST, None, VRF, COUNT, TIMEOUT, SIZE)
        assert "source" not in command


# ── Cisco IOS-XR ─────────────────────────────────────────────────────

class TestCiscoXRTroubleshootBuilder:
    builder = CiscoXRTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert command == "ping vrf MGMT 10.0.0.1 source 192.168.1.1 count 5 timeout 2 size 100"

    def test_no_vrf(self):
        command = self.builder.build_ping(DST, SRC, None, COUNT, TIMEOUT, SIZE)
        assert command.startswith("ping 10.0.0.1")
        assert "vrf" not in command


# ── Arista EOS ───────────────────────────────────────────────────────

class TestAristaEOSTroubleshootBuilder:
    builder = AristaEOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert command == "ping 10.0.0.1 source 192.168.1.1 repeat 5 size 100 vrf MGMT"

    def test_no_vrf(self):
        command = self.builder.build_ping(DST, SRC, None, COUNT, TIMEOUT, SIZE)
        assert "vrf" not in command
        assert command.endswith(f"size {SIZE}")


# ── Juniper JunOS ────────────────────────────────────────────────────

class TestJuniperJunOSTroubleshootBuilder:
    builder = JuniperJunOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert "ping 10.0.0.1" in command
        assert "count 5" in command
        assert "source 192.168.1.1" in command
        assert "routing-instance MGMT" in command   # VRF キーワードが異なる
        assert "size 100" in command
        assert "wait 2" in command

    def test_vrf_keyword_is_routing_instance(self):
        command = self.builder.build_ping(DST, None, VRF, COUNT, TIMEOUT, SIZE)
        assert "routing-instance MGMT" in command
        assert "vrf" not in command

    def test_no_vrf(self):
        command = self.builder.build_ping(DST, SRC, None, COUNT, TIMEOUT, SIZE)
        assert "routing-instance" not in command


# ── Palo Alto PAN-OS ─────────────────────────────────────────────────

class TestPaloAltoTroubleshootBuilder:
    builder = PaloAltoTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert command == "ping vrouter MGMT host 10.0.0.1 source 192.168.1.1 count 5"

    def test_no_vrf(self):
        command = self.builder.build_ping(DST, SRC, None, COUNT, TIMEOUT, SIZE)
        assert "vrouter" not in command
        assert command.startswith("ping host")


# ── Cisco ASA ────────────────────────────────────────────────────────

class TestCiscoASATroubleshootBuilder:
    builder = CiscoASATroubleshootBuilder()

    def test_basic_ping(self):
        command = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert command == "ping 10.0.0.1"

    def test_src_and_vrf_ignored(self):
        # ASA は source / VRF を無視する
        command_with = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        command_without = self.builder.build_ping(DST, None, None, COUNT, TIMEOUT, SIZE)
        assert command_with == command_without


# ── Fortinet FortiOS ─────────────────────────────────────────────────

class TestFortinetTroubleshootBuilder:
    builder = FortinetTroubleshootBuilder()

    def test_returns_list(self):
        commands = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert isinstance(commands, list)

    def test_full_options(self):
        commands = self.builder.build_ping(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)
        assert any("ping-options source 192.168.1.1" in c for c in commands)
        assert any("ping-options count 5" in c for c in commands)
        assert any("ping-options timeout 2" in c for c in commands)
        assert any("ping-options data-size 100" in c for c in commands)
        assert commands[-1] == "execute ping 10.0.0.1"

    def test_no_src_ip_skips_source_option(self):
        commands = self.builder.build_ping(DST, None, VRF, COUNT, TIMEOUT, SIZE)
        assert not any("ping-options source" in c for c in commands)

    def test_last_command_is_execute_ping(self):
        commands = self.builder.build_ping(DST, SRC, None, COUNT, TIMEOUT, SIZE)
        assert commands[-1] == f"execute ping {DST}"


# ── Cisco IOS / IOS-XE traceroute ────────────────────────────────────

class TestCiscoIOSTroubleshootBuilderTraceroute:
    builder = CiscoIOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert command == "traceroute vrf MGMT 10.0.0.1 source 192.168.1.1 probe 3 timeout 2 ttl 1 30"

    def test_no_vrf(self):
        command = self.builder.build_traceroute(DST, SRC, None, PROBE, TIMEOUT, MAX_TTL)
        assert command.startswith("traceroute 10.0.0.1")
        assert "vrf" not in command

    def test_no_src_ip(self):
        command = self.builder.build_traceroute(DST, None, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "source" not in command

    def test_minimal(self):
        command = self.builder.build_traceroute(DST, None, None, PROBE, TIMEOUT, MAX_TTL)
        assert command == "traceroute 10.0.0.1 probe 3 timeout 2 ttl 1 30"


# ── Cisco NX-OS traceroute ────────────────────────────────────────────

class TestCiscoNXOSTroubleshootBuilderTraceroute:
    builder = CiscoNXOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "traceroute 10.0.0.1" in command
        assert "source 192.168.1.1" in command
        assert "vrf MGMT" in command
        # NX-OS does not support probe or timeout options
        assert "probe" not in command
        assert "timeout" not in command

    def test_max_ttl_ignored(self):
        # NX-OS does not support max-ttl, probe, or timeout
        command = self.builder.build_traceroute(DST, None, None, PROBE, TIMEOUT, MAX_TTL)
        assert str(MAX_TTL) not in command
        assert "probe" not in command
        assert "timeout" not in command

    def test_no_vrf(self):
        command = self.builder.build_traceroute(DST, SRC, None, PROBE, TIMEOUT, MAX_TTL)
        assert "vrf" not in command

    def test_no_src_ip(self):
        command = self.builder.build_traceroute(DST, None, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "source" not in command


# ── Cisco IOS-XR traceroute ───────────────────────────────────────────

class TestCiscoXRTroubleshootBuilderTraceroute:
    builder = CiscoXRTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert command == "traceroute vrf MGMT 10.0.0.1 source 192.168.1.1 probe 3 timeout 2 max-ttl 30"

    def test_no_vrf(self):
        command = self.builder.build_traceroute(DST, SRC, None, PROBE, TIMEOUT, MAX_TTL)
        assert command.startswith("traceroute 10.0.0.1")
        assert "vrf" not in command

    def test_max_ttl_present(self):
        command = self.builder.build_traceroute(DST, None, None, PROBE, TIMEOUT, MAX_TTL)
        assert f"max-ttl {MAX_TTL}" in command


# ── Arista EOS traceroute ─────────────────────────────────────────────

class TestAristaEOSTroubleshootBuilderTraceroute:
    builder = AristaEOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "traceroute 10.0.0.1" in command
        assert "source 192.168.1.1" in command
        assert f"probe {PROBE}" in command
        assert f"maxttl {MAX_TTL}" in command

    def test_timeout_ignored(self):
        # Arista does not support a timeout option
        command = self.builder.build_traceroute(DST, None, None, PROBE, TIMEOUT, MAX_TTL)
        assert "timeout" not in command

    def test_no_src_ip(self):
        command = self.builder.build_traceroute(DST, None, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "source" not in command


# ── Juniper JunOS traceroute ──────────────────────────────────────────

class TestJuniperJunOSTroubleshootBuilderTraceroute:
    builder = JuniperJunOSTroubleshootBuilder()

    def test_full_options(self):
        command = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "traceroute 10.0.0.1" in command
        assert "source 192.168.1.1" in command
        assert "routing-instance MGMT" in command
        assert f"probe-count {PROBE}" in command
        assert f"wait {TIMEOUT}" in command
        assert f"ttl {MAX_TTL}" in command

    def test_vrf_keyword_is_routing_instance(self):
        command = self.builder.build_traceroute(DST, None, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "routing-instance MGMT" in command
        assert "vrf" not in command

    def test_no_vrf(self):
        command = self.builder.build_traceroute(DST, SRC, None, PROBE, TIMEOUT, MAX_TTL)
        assert "routing-instance" not in command


# ── Palo Alto PAN-OS traceroute ───────────────────────────────────────

class TestPaloAltoTroubleshootBuilderTraceroute:
    builder = PaloAltoTroubleshootBuilder()

    def test_basic(self):
        command = self.builder.build_traceroute(DST, None, None, PROBE, TIMEOUT, MAX_TTL)
        assert command == "traceroute host 10.0.0.1"

    def test_with_src_ip(self):
        command = self.builder.build_traceroute(DST, SRC, None, PROBE, TIMEOUT, MAX_TTL)
        assert command == "traceroute host 10.0.0.1 source 192.168.1.1"

    def test_vrf_ignored(self):
        # PAN-OS traceroute does not support vrouter
        command = self.builder.build_traceroute(DST, None, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert "vrouter" not in command


# ── Cisco ASA traceroute ──────────────────────────────────────────────

class TestCiscoASATroubleshootBuilderTraceroute:
    builder = CiscoASATroubleshootBuilder()

    def test_basic(self):
        command = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert command == "traceroute 10.0.0.1"

    def test_src_and_vrf_ignored(self):
        command_with = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        command_without = self.builder.build_traceroute(DST, None, None, PROBE, TIMEOUT, MAX_TTL)
        assert command_with == command_without


# ── Fortinet FortiOS traceroute ───────────────────────────────────────

class TestFortinetTroubleshootBuilderTraceroute:
    builder = FortinetTroubleshootBuilder()

    def test_returns_str(self):
        result = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert isinstance(result, str)

    def test_command(self):
        command = self.builder.build_traceroute(DST, SRC, VRF, PROBE, TIMEOUT, MAX_TTL)
        assert command == "execute traceroute 10.0.0.1"


# ── build_telnet は NotImplementedError ──────────────────────────────

class TestNotImplementedMethods:
    def test_telnet_raises(self):
        builder = CiscoIOSTroubleshootBuilder()
        with pytest.raises(NotImplementedError):
            builder.build_telnet("10.0.0.1", 22, VRF, SRC)
