from neteye.arp_entry.models import ArpEntry

CISCO_MAC = "0000.0c07.ac01"
VMWARE_MAC = "0050.5600.0001"


def test_vendor_is_looked_up_from_the_mac():
    assert ArpEntry(ip_address="10.0.0.1", mac_address=CISCO_MAC, interface_id="x").vendor == "Cisco Systems, Inc"


def test_incomplete_entry_has_no_vendor():
    assert ArpEntry(ip_address="10.0.0.1", mac_address="Incomplete", interface_id="x").vendor == ""


def test_vendor_passed_in_is_replaced_by_the_lookup():
    # The import fills missing fields from the previous row, so a stale vendor can be passed in.
    entry = ArpEntry(ip_address="10.0.0.1", mac_address=CISCO_MAC, interface_id="x", vendor="VMware, Inc.")
    assert entry.vendor == "Cisco Systems, Inc"


def test_vendor_follows_a_changed_mac():
    entry = ArpEntry(ip_address="10.0.0.1", mac_address="Incomplete", interface_id="x")
    entry.mac_address = CISCO_MAC
    assert entry.vendor == "Cisco Systems, Inc"
    entry.mac_address = VMWARE_MAC
    assert entry.vendor == "VMware, Inc."
    entry.mac_address = "Incomplete"
    assert entry.vendor == ""
