from neteye.interface.models import Interface
from neteye.serial.models import Serial
from neteye.arp_entry.models import ArpEntry
from neteye.cable.models import Cable
from neteye.lib.utils.get_records_by_node import get_records_by_node


node_id = 'c2070874-8b54-4b15-a90d-f18acf4fb8b5'
print(get_records_by_node(Interface, node_id))
print(get_records_by_node(Serial, node_id))
print(get_records_by_node(ArpEntry, node_id))
print(get_records_by_node(Cable, node_id))

