from neteye.base.models import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship, backref
import netmiko
from neteye.interface.models import Interface
from neteye.serial.models import Serial

class Node(Base):
    __tablename__ = 'nodes'

    hostname = Column(String, unique=True, nullable=True)
    description = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    device_type = Column(String)
    model = Column(String)
    os_type = Column(String)
    os_version = Column(String)
    username = Column(String)
    password = Column(String)
    enable = Column(String)

    interfaces = relationship('Interface', backref='nodes', lazy='joined')
    serials = relationship('Serial', backref='nodes', lazy='joined')

    def __repr__(self):
        return "<Node id={id} hostname={hostname} ip_address={ip_address}".format(id=self.id, hostname=self.hostname, ip_address=self.ip_address)

    def gen_params(self, device_type='autodetect'):
        return {
            'device_type': device_type,
            'ip': self.ip_address,
            'username': self.username,
            'password': self.password,
            'secret': self.enable
        }

    def gen_conn(self):
        try:
            return netmiko.ConnectHandler(**self.gen_params())
        except netmiko.ssh_exception.NetMikoTimeoutException as err:
            return netmiko.ConnectHandler(**self.gen_params(device_type='cisco_ios_telnet'))
