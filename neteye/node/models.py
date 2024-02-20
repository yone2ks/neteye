import json

import napalm
import netmiko
import scrapli
from netmiko.ssh_autodetect import SSHDetect
from scrapli import Scrapli
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship

from neteye.base.models import Base
from neteye.extensions import connection_pool, db, ntc_template_utils, settings
from neteye.interface.models import Interface
from neteye.lib.device_type_to_driver_mapping.device_type_to_driver_mapping import \
    DeviceTypeToDriverMapping
from neteye.serial.models import Serial
from neteye.history.model_command_history import CommandHistory
from neteye.lib.scrapli_community_helper.scrapli_community_helper import ScrapliCommunityHelper

DRIVER_TYPE_NETMIKO = "netmiko"
DRIVER_TYPE_SCRAPLI = "scrapli"
DRIVER_TYPE_NAPALM = "napalm"
NOT_SUPPORTED = "not supported"
napalm_driver_mapping = DeviceTypeToDriverMapping(DRIVER_TYPE_NAPALM)
scrapli_driver_mapping = DeviceTypeToDriverMapping(DRIVER_TYPE_SCRAPLI)
NETMIKO_PLATFORMS = netmiko.platforms
SCRAPLI_DRIVERS = list(Scrapli.CORE_PLATFORM_MAP.keys()) + list(ScrapliCommunityHelper.COMMUNITY_PLATFORM.keys())
NAPALM_DRIVERS = napalm.SUPPORTED_DRIVERS


class Node(Base):
    __tablename__ = "nodes"

    hostname = Column(String, unique=True, nullable=False)
    description = Column(String, default="")
    ip_address = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    device_type = Column(String)
    scrapli_driver = Column(String)
    napalm_driver = Column(String)
    model = Column(String)
    os_type = Column(String)
    os_version = Column(String)
    username = Column(String)
    password = Column(String)
    enable = Column(String)
    interfaces = relationship(
        "Interface",
        backref="nodes",
        lazy="joined",
        cascade="save-update, merge, delete",
    )
    serials = relationship(
        "Serial", backref="nodes", lazy="joined", cascade="save-update, merge, delete"
    )

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        if self.device_type == "autodetect": self.detect_device_type()
        self.detect_napalm_driver()
        self.detect_scrapli_driver()

    def __repr__(self):
        return "<Node id={id} hostname={hostname} ip_address={ip_address}".format(
            id=self.id, hostname=self.hostname, ip_address=self.ip_address
        )

    def exists(hostname):
        return Node.query.filter_by(hostname=hostname).scalar() != None

    def gen_netmiko_params(self, global_delay_factor=1, timeout=10, keepalive=10):
        return {
            "device_type": self.device_type,
            "ip": self.ip_address,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "secret": self.enable,
            "global_delay_factor": global_delay_factor,
            "timeout": timeout,
            "keepalive": keepalive,
        }

    def gen_scrapli_params(self, timeout_socket=10, timeout_transport=10, timeout_ops=10):
        params = {
                "host": self.ip_address,
                "port": self.port,
                "auth_username": self.username,
                "auth_password": self.password,
                "auth_strict_key": False,
                "platform": self.scrapli_driver,
                "transport": "telnet" if "telnet" in self.device_type else "ssh2",
                "timeout_socket": timeout_socket,
                "timeout_transport": timeout_transport,
                "timeout_ops": timeout_ops
        }

        if ScrapliCommunityHelper.is_community_platform(self.scrapli_driver) and (not ScrapliCommunityHelper.is_network_driver(self.scrapli_driver)):
            return params
        else:
            params["auth_secondary"] = self.enable
            return params

    def gen_napalm_params(self, timeout=10):
        enable_param = "enable_password" if self.napalm_driver == "eos" else "secret"
        optional_args = {enable_param: self.enable, "port": self.port}
        return {
            "hostname": self.ip_address,
            "username": self.username,
            "password": self.password,
            "optional_args": optional_args,
            "timeout": timeout
        }

    def detect_device_type(self):
        try:
            self.device_type = SSHDetect(
                **self.gen_netmiko_params()
            ).autodetect()
        except (
            netmiko.ssh_exception.NetMikoTimeoutException,
            netmiko.ssh_exception.SSHException,
        ) as err:
            self.device_type = "cisco_ios_telnet"
            self.port = 23

    def detect_scrapli_driver(self):
        if self.device_type in scrapli_driver_mapping.mapping_dict.keys():
            self.scrapli_driver = scrapli_driver_mapping.mapping_dict[self.device_type]
        else:
            self.scrapli_driver = NOT_SUPPORTED

    def detect_napalm_driver(self):
        if self.device_type in napalm_driver_mapping.mapping_dict.keys():
            self.napalm_driver = napalm_driver_mapping.mapping_dict[self.device_type]
        else:
            self.napalm_driver = NOT_SUPPORTED

    def command_with_history(self, command, session_user):
        result = self.command(command)
        command_history = CommandHistory(username=session_user, node_id=self.id, hostname=self.hostname, command=command, result=json.dumps(result))
        command_history.add()
        return result

    def command(self, command):
        if not self.scrapli_driver == NOT_SUPPORTED:
            return self.scrapli_command(command)
        else:
            return self.netmiko_command(command)

    def raw_command_with_history(self, command, session_user):
        result = self.raw_command(command)
        command_history = CommandHistory(username=session_user, node_id=self.id, hostname=self.hostname, command=command, result=json.dumps(result))
        command_history.add()
        return result

    def raw_command(self, command):
        if not self.scrapli_driver == NOT_SUPPORTED:
            return self.scrapli_raw_command(command)
        else:
            return self.netmiko_raw_command(command)

    def netmiko_command_with_history(self, command, session_user):
        result = self.netmiko_command(command)
        command_history = CommandHistory(username=session_user, node_id=self.id, hostname=self.hostname, command=command, result=json.dumps(result))
        command_history.add()
        return result

    def netmiko_command(self, command):
        if not connection_pool.exists(self, DRIVER_TYPE_NETMIKO):
            connection_pool.add_connection(self, DRIVER_TYPE_NETMIKO)
        conn = connection_pool.get_connection(self, DRIVER_TYPE_NETMIKO)
        return conn.send_command(command, use_textfsm=True)

    def netmiko_raw_command_with_history(self, command, session_user):
        result = self.netmiko_raw_command(command)
        command_history = CommandHistory(username=session_user, node_id=self.id, hostname=self.hostname, command=command, result=json.dumps(result))
        command_history.add()
        return result

    def netmiko_raw_command(self, command):
        if not connection_pool.exists(self, DRIVER_TYPE_NETMIKO):
            connection_pool.add_connection(self, DRIVER_TYPE_NETMIKO)
        conn = connection_pool.get_connection(self, DRIVER_TYPE_NETMIKO)
        return conn.send_command(command, use_textfsm=False)

    def scrapli_command_with_history(self, command, session_user):
        result = self.scrapli_command(command)
        command_history = CommandHistory(username=session_user, node_id=self.id, hostname=self.hostname, command=command, result=json.dumps(result))
        command_history.add()
        return result

    def scrapli_command(self, command):
        if not connection_pool.exists(self, DRIVER_TYPE_SCRAPLI):
            connection_pool.add_connection(self, DRIVER_TYPE_SCRAPLI)
        else:
            connection_pool.recreate_connection(self, DRIVER_TYPE_SCRAPLI)
        conn = connection_pool.get_connection(self, DRIVER_TYPE_SCRAPLI)
        response = conn.send_command(command)
        if not ScrapliCommunityHelper.is_network_driver(self.scrapli_driver):
            response.textfsm_platform = self.device_type
        parsed_output = response.textfsm_parse_output()
        if parsed_output:
            return parsed_output
        return response.result

    def scrapli_raw_command_with_history(self, command, session_user):
        result = self.scrapli_raw_command(command)
        command_history = CommandHistory(username=session_user, node_id=self.id, hostname=self.hostname, command=command, result=json.dumps(result))
        command_history.add()
        return result

    def scrapli_raw_command(self, command):
        if not connection_pool.exists(self, DRIVER_TYPE_SCRAPLI):
            connection_pool.add_connection(self, DRIVER_TYPE_SCRAPLI)
        conn = connection_pool.get_connection(self, DRIVER_TYPE_SCRAPLI)
        return conn.send_command(command).result

    def napalm_get_facts(self):
        if not connection_pool.exists(self, DRIVER_TYPE_NAPALM):
            connection_pool.add_connection(self, DRIVER_TYPE_NAPALM)
        conn = connection_pool.get_connection(self, DRIVER_TYPE_NAPALM)
        return conn.get_facts()

    def napalm_get_interfaces(self):
        if not connection_pool.exists(self, DRIVER_TYPE_NAPALM):
            connection_pool.add_connection(self, DRIVER_TYPE_NAPALM)
        conn = connection_pool.get_connection(self, DRIVER_TYPE_NAPALM)
        return conn.get_interfaces()

    def gen_connection(self, driver_type):
        if driver_type == DRIVER_TYPE_NAPALM:
            return self.gen_napalm_connection()
        elif driver_type == DRIVER_TYPE_SCRAPLI:
            return self.gen_scrapli_connection()
        else:
            return self.gen_netmiko_connection()

    def gen_netmiko_connection(self):
        return netmiko.ConnectHandler(**self.gen_netmiko_params(
            settings["default"]["NETMIKO_GLOBAL_DELAY_FACTOR"],
            settings["default"]["NETMIKO_TIMEOUT"]))

    def gen_scrapli_connection(self):
        conn = scrapli.Scrapli(**self.gen_scrapli_params(
            settings["default"]["SCRAPLI_TIMEOUT_SOCKET"],
            settings["default"]["SCRAPLI_TIMEOUT_TRANSPORT"],
            settings["default"]["SCRAPLI_TIMEOUT_OPS"]))
        conn.open()
        return conn

    def gen_napalm_connection(self):
        driver = napalm.get_network_driver(self.napalm_driver)
        conn = driver(**self.gen_napalm_params(
            settings["default"]["NAPALM_TIMEOUT"]))
        conn.open()
        return conn
