from sqlalchemy_continuum import transaction_class, version_class

from neteye.arp_entry.models import ArpEntry
from neteye.cable.models import Cable
from neteye.interface.models import Interface
from neteye.node.models import Node
from neteye.serial.models import Serial

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

OPERATION_TYPE = {0: "INSERT", 1: "UPDATE", 2: "DELETE"}
