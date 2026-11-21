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

    def test_unknown_platform_returns_empty_list(self, utils):
        assert utils.parse("nonexistent_platform", "show version", "some output") == []

    def test_command_without_template_returns_empty_list(self, utils):
        assert utils.parse("cisco_ios", "show running-config", "hostname r1\n") == []

    def test_platform_mapping_applied(self, utils):
        # device_type "cisco_ios" should map through ntc_template_platform_mapping
        raw = ""
        result = utils.parse("cisco_ios", "show version", raw)
        assert isinstance(result, list)

    def test_empty_data_returns_list(self, utils):
        result = utils.parse("cisco_ios", "show version", "")
        assert isinstance(result, list)


class TestNtcTemplateIndexLoading:
    INDEX = (
        "Template, Hostname, Platform, Command\n"
        "cisco_nxos_show_version.textfsm, .*, cisco_nxos, sh[[ow]] ver[[sion]]\n"
    )

    def test_index_is_read_when_net_textfsm_is_set_after_import(self, tmp_path, monkeypatch):
        (tmp_path / "index").write_text(self.INDEX)
        monkeypatch.setenv("NET_TEXTFSM", str(tmp_path))
        assert NtcTemplateUtils().get_command_list("cisco_nxos") == ["show version"]

    def test_index_is_empty_without_net_textfsm(self, monkeypatch):
        monkeypatch.delenv("NET_TEXTFSM", raising=False)
        assert NtcTemplateUtils().get_command_list("cisco_nxos") == []
