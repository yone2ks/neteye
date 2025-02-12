from netaddr import *
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship

from neteye.base.models import Base
from neteye.interface.models import Interface


class ArpEntry(Base):
    __tablename__ = "arp_entries"

    ATTRIBUTES = {"ip_address", "mac_address", "interface_id", "protocol", "arp_type", "vendor"}
    KEY = "ip_address"

    ip_address = Column(String, nullable=False)
    mac_address = Column(String, nullable=False)
    interface_id = Column(String, ForeignKey("interfaces.id", ondelete="CASCADE"), nullable=False)
    interface = relationship("Interface")
    protocol = Column(String)
    arp_type = Column(String)
    vendor = Column(String)

    def __init__(self, **kwargs):
        super(ArpEntry, self).__init__(**kwargs)
        try:
            if valid_mac(self.mac_address):
                self.vendor = EUI(self.mac_address, dialect=mac_unix_expanded).oui.registration().org
            else:
                self.vendor = ""
        except NotRegisteredError as err:
            self.vendor = ""


    def __repr__(self):
        return "<ARP Entry id={id} ip_address={ip_address} mac_address={mac_address}".format(
            id=self.id, ip_address=self.ip_address, mac_address=self.mac_address
        )

    def exists(ip_address, interface_id):
        return ArpEntry.query.filter_by(ip_address=ip_address, interface_id=interface_id).scalar() != None


    def to_dict(self):
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "interface_id": self.interface_id,
            "protocol": self.protocol,
            "arp_type": self.arp_type,
            "vendor": self.vendor,
        }