from netaddr import *
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import backref, relationship, validates

from neteye.base.models import Base
from neteye.interface.models import Interface


def lookup_vendor(mac_address):
    """Return the OUI vendor of the MAC address, or "" when it is not a MAC (such as Incomplete) or not registered."""
    if not mac_address or not valid_mac(mac_address):
        return ""
    try:
        return EUI(mac_address, dialect=mac_unix_expanded).oui.registration().org
    except NotRegisteredError:
        return ""


class ArpEntry(Base):
    __tablename__ = "arp_entries"

    # vendor is derived from mac_address (see _update_vendor); do not source it from an import mapping.
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
        # A vendor passed in kwargs (for example carried over from an earlier row) may be stale.
        self.vendor = lookup_vendor(self.mac_address)

    @validates("mac_address")
    def _update_vendor(self, key, mac_address):
        # Keep the vendor in step when an import replaces the MAC of an existing entry
        # (for example Incomplete -> a resolved MAC, or a replaced host on the same IP).
        self.vendor = lookup_vendor(mac_address)
        return mac_address


    def __repr__(self):
        return "<ARP Entry id={id} ip_address={ip_address} mac_address={mac_address}".format(
            id=self.id, ip_address=self.ip_address, mac_address=self.mac_address
        )

    @staticmethod
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