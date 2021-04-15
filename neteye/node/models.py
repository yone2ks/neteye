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

NETMIKO_PLATFORMS = netmiko.platforms
NAPALM_DRIVERS = napalm.SUPPORTED_DRIVERS
SCRAPLI_DRIVERS = napalm.SUPPORTED_DRIVERS

class Node(Base):
    __tablename__ = "nodes"

    hostname = Column(String, unique=True, nullable=False)
    description = Column(String)
    ip_address = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    device_type = Column(String)
    napalm_driver = Column(String)
    scrapli_driver = Column(String)
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

    def gen_netmiko_params(self, global_delay_factor=1, timeout=10):
        return {
            "device_type": self.device_type,
            "ip": self.ip_address,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "secret": self.enable,
            "global_delay_factor": global_delay_factor,
            "timeout": timeout,
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

    def detect_napalm_driver(self):
        napalm_driver_mapping = DeviceTypeToDriverMapping("napalm")
        if self.device_type in napalm_driver_mapping.mapping_dict.keys():
            self.napalm_driver = napalm_driver_mapping.mapping_dict[self.device_type]
        else:
            self.napalm_driver = "not detected"

    def detect_scrapli_driver(self):
        scrapli_driver_mapping = DeviceTypeToDriverMapping("scrapli")
        if self.device_type in scrapli_driver_mapping.mapping_dict.keys():
            self.scrapli_driver = scrapli_driver_mapping.mapping_dict[self.device_type]
        else:
            self.scrapli_driver = "not detected"

    def command(self, command):
        if not connection_pool.connection_exists(self.ip_address):
            connection_pool.add_connection(self.gen_netmiko_params(settings["default"]["NETMIKO_GLOBAL_DELAY_FACTOR"], settings["default"]["NETMIKO_TIMEOUT"]))
        conn = connection_pool.get_connection(self.ip_address)
        conn.enable()
        return conn.send_command(command, use_textfsm=True)

    def raw_command(self, command):
        if not connection_pool.connection_exists(self.ip_address):
            connection_pool.add_connection(self.gen_netmiko_params(settings["default"]["NETMIKO_GLOBAL_DELAY_FACTOR"], settings["default"]["NETMIKO_TIMEOUT"]))
        conn = connection_pool.get_connection(self.ip_address)
        conn.enable()
        return conn.send_command(command, use_textfsm=False)

    def gen_conn(self):
        return netmiko.ConnectHandler(**self.gen_netmiko_params())
