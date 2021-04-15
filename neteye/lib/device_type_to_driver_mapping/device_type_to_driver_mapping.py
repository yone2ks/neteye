import json
import os


class DeviceTypeToDriverMapping:
    MAPPING_DIR = os.path.dirname(__file__) + "/mappings/"
    PREFIX = "netmiko_to_"
    SUFFIX = "_mapping.json"
    package_name: str
    mapping_dict: dict

    def __init__(self, package_name):
        self.package_name = package_name
        with open(
            self.MAPPING_DIR + self.PREFIX + self.package_name + self.SUFFIX, "r"
        ) as mapping_json:
            self.mapping_dict = json.load(mapping_json)
