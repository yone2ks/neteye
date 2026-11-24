import logging

import pytest

from neteye.lib.intf_abbrev import intf_abbrev
from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter

DEVICE_TYPES = ["cisco_ios", "cisco_ios_telnet", "cisco_xe", "cisco_xr", "cisco_nxos"]


@pytest.fixture
def converter():
    return IntfAbbrevConverter("cisco_ios")


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Gi1/0/1", "GigabitEthernet1/0/1"),
        ("Eth1/1", "Ethernet1/1"),
        ("Et0/0", "Ethernet0/0"),
        ("Te1/0/1", "TenGigabitEthernet1/0/1"),
        ("Fo1/0/1", "FortyGigabitEthernet1/0/1"),
        ("Po1", "Port-channel1"),
        ("Vl10", "Vlan10"),
    ],
)
def test_normalization_expands_abbreviated_names(converter, name, expected):
    assert converter.normalization(name) == expected


@pytest.mark.parametrize(
    "name",
    ["GigabitEthernet1/0/1", "Ethernet1/1", "Vlan10", "Port-channel1", "mgmt0", "MgmtEth0/RP0/CPU0/0", "Ap1/0/1"],
)
def test_normalization_keeps_names_that_are_not_abbreviated(converter, name):
    assert converter.normalization(name) == name


@pytest.mark.parametrize("name", ["", "17", "1/1", "/"])
def test_normalization_does_not_fail_without_letters(converter, name):
    assert converter.normalization(name) == name


@pytest.mark.parametrize(
    "name, expected",
    [
        ("GigabitEthernet1/0/1", "Gi1/0/1"),
        ("TenGigabitEthernet1/0/1", "Te1/0/1"),
        ("Vlan10", "Vl10"),
    ],
)
def test_to_abbrev_shortens_long_names(converter, name, expected):
    assert converter.to_abbrev(name) == expected


@pytest.mark.parametrize("long_name, expected", [("Ethernet1/1", "Eth1/1"), ("Port-channel1", "Po1")])
def test_to_abbrev_picks_the_last_alias_listed_in_the_template(converter, long_name, expected):
    # Several abbreviations share one long name (Et/Eth, PortCh/Po). The one listed last in the
    # template wins, so reordering the template changes the label; this test makes that visible.
    assert converter.to_abbrev(long_name) == expected


def test_to_abbrev_uses_the_longest_matching_prefix(converter):
    # "GigabitEthernet" and "Ethernet" also appear inside this name; the prefix must win.
    assert converter.to_abbrev("FortyGigabitEthernet1/0/1") == "Fo1/0/1"


@pytest.mark.parametrize("name", ["Gi1/0/1", "Mgmt0", "MgmtEth0/RP0/CPU0/0", "Hu0/0/0/1", ""])
def test_to_abbrev_returns_the_input_when_nothing_matches(converter, name):
    assert converter.to_abbrev(name) == name


def test_to_long_returns_the_input_when_nothing_matches(converter):
    assert converter.to_long("Mgmt0") == "Mgmt0"


def test_to_long_only_replaces_the_prefix(converter):
    assert converter.to_long("Gi1/0/Gi1") == "GigabitEthernet1/0/Gi1"


@pytest.mark.parametrize("device_type", DEVICE_TYPES)
def test_every_template_round_trips_its_long_names(device_type):
    converter = IntfAbbrevConverter(device_type)
    for long_name in converter.long_to_abbrev:
        assert converter.to_long(converter.to_abbrev(long_name + "1/1")) == long_name + "1/1"


def test_missing_template_is_logged_once(caplog):
    intf_abbrev._missing_template_paths.discard(f"{IntfAbbrevConverter.TEMPLATE_DIR}no_such_device.json")
    with caplog.at_level(logging.WARNING, logger=intf_abbrev.logger.name):
        for _ in range(3):
            with pytest.raises(FileNotFoundError):
                IntfAbbrevConverter("no_such_device")
    assert len([r for r in caplog.records if "no_such_device" in r.getMessage()]) == 1
