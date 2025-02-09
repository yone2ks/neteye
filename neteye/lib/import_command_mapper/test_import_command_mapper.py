import pytest
import os
import json
from import_command_mapper import ImportCommandMapper, IMPORT_INTERFACE, IMPORT_SERIAL, IMPORT_NODE, IMPORT_ARP_ENTRY

import_command_mapper = ImportCommandMapper("cisco_ios")

print(import_command_mapper.get_mappings(import_type=IMPORT_INTERFACE))
print(import_command_mapper.get_commands(import_type=IMPORT_INTERFACE))
print(import_command_mapper.get_command(import_type=IMPORT_INTERFACE, command="show ip int brief"))
print(import_command_mapper.get_fields(IMPORT_INTERFACE, "show ip int brief"))
print(import_command_mapper.get_source(IMPORT_INTERFACE, "show ip int brief", "name"))
print(import_command_mapper.get_normalizer(IMPORT_INTERFACE, "show ip int brief", "name"))
print(import_command_mapper.get_index(IMPORT_INTERFACE, "show ip int brief"))
print(import_command_mapper.get_index(IMPORT_NODE, "show version"))