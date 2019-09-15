from neteye.base.models import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship, backref
import netmiko
from netmiko.ssh_autodetect import SSHDetect
from neteye.interface.models import Interface
from neteye.serial.models import Serial

class ArpEntry(Base):
    __tablename__ = 'arp_entries'

    ip_address = Column(String, nullable=False)
    mac_address = Column(String, nullable=False)
    interface_id = Column(Integer, ForeignKey('interfaces.id'))
    protocol = Column(String)
    arp_type = Column(String)
    vendor = Column(String)

    def __repr__(self):
        return "<ARP Entry id={id} ip_address={ip_address} mac_address={mac_address}".format(id=self.id, ip_address=self.ip_address, mac_address=self.mac_address)

    def exists(ip_address):
        return ArpEntry.query.filter_by(ip_address=ip_address).scalar() != None
