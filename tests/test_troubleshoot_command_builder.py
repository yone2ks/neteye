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

DST = "10.0.0.1"
SRC = "192.168.1.1"
VRF = "MGMT"
COUNT = 5
TIMEOUT = 2
SIZE = 100


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


# ── build_traceroute / build_telnet は NotImplementedError ──────────

class TestNotImplementedMethods:
    def test_traceroute_raises(self):
        builder = CiscoIOSTroubleshootBuilder()
        with pytest.raises(NotImplementedError):
            builder.build_traceroute(DST, SRC, VRF, COUNT, TIMEOUT, SIZE)

    def test_telnet_raises(self):
        builder = CiscoIOSTroubleshootBuilder()
        with pytest.raises(NotImplementedError):
            builder.build_telnet("10.0.0.1", 22, VRF, SRC)
