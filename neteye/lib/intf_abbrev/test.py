from intf_abbrev import IntfAbbrevConverter

abbrev_converter = IntfAbbrevConverter("cisco_ios")
print(abbrev_converter.to_abbrev("GigabitEthernet2/0/1"))
print(abbrev_converter.to_long("Gi0/1"))
