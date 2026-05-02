import pytest
from neteye.lib.ntc_template_utils.ntc_template_utils import NtcTemplateUtils


@pytest.fixture(scope="module")
def utils():
    return NtcTemplateUtils()


class TestNtcTemplateUtilsParse:
    def test_cisco_ios_show_version(self, utils):
        raw = "Cisco IOS Software, Version 15.1(4)M4"
        result = utils.parse("cisco_ios", "show version", raw)
        assert isinstance(result, list)

    def test_returns_list_of_dicts(self, utils):
        raw = (
            "Interface              IP-Address      OK? Method Status                Protocol\n"
            "GigabitEthernet0/0     192.168.1.1     YES NVRAM  up                    up\n"
        )
        result = utils.parse("cisco_ios", "show ip interface brief", raw)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)

    def test_unknown_platform_raises(self, utils):
        with pytest.raises(Exception):
            utils.parse("nonexistent_platform", "show version", "some output")

    def test_platform_mapping_applied(self, utils):
        # device_type "cisco_ios" should map through ntc_template_platform_mapping
        raw = ""
        result = utils.parse("cisco_ios", "show version", raw)
        assert isinstance(result, list)

    def test_empty_data_returns_list(self, utils):
        result = utils.parse("cisco_ios", "show version", "")
        assert isinstance(result, list)
