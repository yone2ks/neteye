from sqlalchemy_continuum import transaction_class, version_class
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import backref, relationship


from neteye.base.models import Base
from neteye.arp_entry.models import ArpEntry
from neteye.cable.models import Cable
from neteye.interface.models import Interface
from neteye.node.models import Node
from neteye.serial.models import Serial
from neteye.history.history_utils import HistoryUtils

# Create version and transaction classes for history tracking
node_version = version_class(Node)
node_transaction = transaction_class(Node)
interface_version = version_class(Interface)
interface_transaction = transaction_class(Interface)
serial_version = version_class(Serial)
serial_transaction = transaction_class(Serial)
cable_version = version_class(Cable)
cable_transaction = transaction_class(Cable)
arp_entry_version = version_class(ArpEntry)
arp_entry_transaction = transaction_class(ArpEntry)

# Dynamically inject record limit functionality into all history classes
for cls in [
    node_version,
    node_transaction,
    interface_version,
    interface_transaction,
    serial_version,
    serial_transaction,
    cable_version,
    cable_transaction,
    arp_entry_version,
    arp_entry_transaction,
]:
    # Inject utility methods from HistoryUtils
    cls.get_max_records_setting = classmethod(HistoryUtils.get_max_records_setting.__func__)
    cls.enforce_record_limit = classmethod(HistoryUtils.enforce_record_limit.__func__)
    cls.add_with_limit = HistoryUtils.add_with_limit

OPERATION_TYPE = {0: "INSERT", 1: "UPDATE", 2: "DELETE"}
