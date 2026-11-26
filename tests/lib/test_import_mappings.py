import glob
import os

import pytest
import yaml

from neteye.lib.import_command_mapper.import_command_mapper import NORMALIZER_NAMES, ImportCommandMapper
from neteye.lib.utils.neteye_normalizer import normalize_noop

MAPPING_FILES = sorted(glob.glob(os.path.join(ImportCommandMapper.MAPPING_DIR, "*.yml")))
ALLOWED_FIELD_KEYS = {"source", "normalizer", "foreign_key"}


@pytest.mark.parametrize("path", MAPPING_FILES, ids=os.path.basename)
def test_field_definitions_only_use_known_keys(path):
    # A misspelled key (for example "normalize:" instead of "normalizer:") is silently ignored
    # by the mapper, so the normalization never runs. Catch it here.
    with open(path) as mapping_yaml:
        mapping = yaml.safe_load(mapping_yaml)
    for import_type, commands in mapping.items():
        for command in commands:
            for field, definition in command.get("field", {}).items():
                unknown = set(definition) - ALLOWED_FIELD_KEYS
                assert not unknown, f"{os.path.basename(path)} {import_type} {command['command']!r} {field}: {unknown}"
                assert definition.get("normalizer", "noop") in NORMALIZER_NAMES, (
                    f"{os.path.basename(path)} {import_type} {command['command']!r} {field}: {definition['normalizer']!r}"
                )


def test_fortinet_interface_speed_and_duplex_are_normalized():
    mapper = ImportCommandMapper("fortinet")
    command = next(c for c in mapper.get_commands("import_interface") if mapper.get_fields("import_interface", c).get("speed"))
    assert mapper.get_normalizer("import_interface", command, "speed")("1000") == "1Gbps"
    assert mapper.get_normalizer("import_interface", command, "duplex")(" Full ") == "full"


@pytest.mark.parametrize("device_type", ["cisco_ios", "cisco_ios_telnet", "cisco_xe", "cisco_xr", "cisco_nxos"])
@pytest.mark.parametrize("incomplete", ["Incomplete", "INCOMPLETE"])
def test_arp_keeps_incomplete_entries(device_type, incomplete):
    # An unresolved entry shows the device could not resolve the address, which is useful when
    # troubleshooting, so it must be imported. Entries without an age ("-") are still skipped.
    mapper = ImportCommandMapper(device_type)
    command = mapper.get_commands("import_arp_entry")[0]
    rows = [
        {"ip_address": "10.5.6.10", "mac_address": incomplete, "age": "0", "interface": "Vlan1425"},
        {"ip_address": "10.5.6.1", "mac_address": "0011.2233.4455", "age": "1", "interface": "Vlan1425"},
        {"ip_address": "10.5.6.2", "mac_address": "0011.2233.4466", "age": "-", "interface": "Vlan1425"},
    ]
    kept = mapper.filter_ignore_records("import_arp_entry", command, rows)
    assert [row["ip_address"] for row in kept] == ["10.5.6.10", "10.5.6.1"]
    normalize = mapper.get_normalizer("import_arp_entry", command, "mac_address")
    assert normalize(incomplete) == "Incomplete"


def test_nxos_interface_status_comes_from_the_link_state():
    # "status" in the ntc-templates output for NX-OS is the admin state (admin-up/admin-down);
    # the link state is the counterpart of the "status" column on IOS.
    mapper = ImportCommandMapper("cisco_nxos")
    assert mapper.get_source("import_interface", "show ip int brief vrf all", "status") == "link"


@pytest.mark.parametrize("name", sorted(NORMALIZER_NAMES - {"noop"}))
def test_every_listed_normalizer_is_wired_up(name):
    # Keeps NORMALIZER_NAMES and the mapping inside get_normalizer in step.
    mapper = ImportCommandMapper("cisco_ios")
    mapper.mapping_dict = {"import_interface": [{"command": "cmd", "field": {"value": {"source": "v", "normalizer": name}}}]}
    assert mapper.get_normalizer("import_interface", "cmd", "value") is not normalize_noop
