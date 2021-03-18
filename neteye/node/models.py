import netmiko
from netmiko.ssh_autodetect import SSHDetect
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship

from neteye.base.models import Base
from neteye.interface.models import Interface
from neteye.serial.models import Serial


class Node(Base):
    __tablename__ = "nodes"

    hostname = Column(String, unique=True, nullable=False)
    description = Column(String)
    ip_address = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    device_type = Column(String)
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

    def __repr__(self):
        return "<Node id={id} hostname={hostname} ip_address={ip_address}".format(
            id=self.id, hostname=self.hostname, ip_address=self.ip_address
        )

    def exists(hostname):
        return Node.query.filter_by(hostname=hostname).scalar() != None

    def gen_params(self, timeout=10):
        return {
            "device_type": self.device_type,
            "ip": self.ip_address,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "secret": self.enable,
            "timeout": timeout,
        }

    def detect_device_type(self):
        try:
            self.device_type = SSHDetect(
                **self.gen_params()
            ).autodetect()
        except (
            netmiko.ssh_exception.NetMikoTimeoutException,
            netmiko.ssh_exception.SSHException,
        ) as err:
            self.device_type = "cisco_ios_telnet"

    def gen_conn(self):
        return netmiko.ConnectHandler(**self.gen_params())
