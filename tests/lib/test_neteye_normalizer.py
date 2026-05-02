import pytest
from neteye.lib.utils.neteye_normalizer import (
    normalize_duplex,
    normalize_mac_address,
    normalize_mask,
    normalize_speed,
)


class TestNormalizeMacAddress:
    def test_colon_notation(self):
        assert normalize_mac_address("00:1A:2B:3C:4D:5E") == "001a.2b3c.4d5e"

    def test_hyphen_notation(self):
        assert normalize_mac_address("00-1A-2B-3C-4D-5E") == "001a.2b3c.4d5e"

    def test_cisco_notation_unchanged(self):
        assert normalize_mac_address("001a.2b3c.4d5e") == "001a.2b3c.4d5e"

    def test_invalid_mac_returned_as_is(self):
        assert normalize_mac_address("not-a-mac") == "not-a-mac"


class TestNormalizeMask:
    def test_dotted_quad_to_cidr(self):
        assert normalize_mask("255.255.255.0") == "24"

    def test_dotted_quad_16(self):
        assert normalize_mask("255.255.0.0") == "16"

    def test_cidr_unchanged(self):
        assert normalize_mask("24") == "24"

    def test_cidr_string_unchanged(self):
        assert normalize_mask("16") == "16"


class TestNormalizeSpeed:
    @pytest.mark.parametrize("raw,expected", [
        ("10", "10Mbps"),
        ("100", "100Mbps"),
        ("1000", "1Gbps"),
        ("10000", "10Gbps"),
        ("100000", "100Gbps"),
        ("1Gbps", "1Gbps"),
        ("10gbps", "10Gbps"),
        ("100mbps", "100Mbps"),
    ])
    def test_speed_normalization(self, raw, expected):
        assert normalize_speed(raw) == expected


class TestNormalizeDuplex:
    def test_full_lowercase(self):
        assert normalize_duplex("Full") == "full"

    def test_half_with_spaces(self):
        assert normalize_duplex("  half  ") == "half"

    def test_already_lowercase(self):
        assert normalize_duplex("full") == "full"
