import json
import os
import re


class IntfAbbrevConverter:
    TEMPLATE_DIR = os.path.dirname(__file__) + "/templates/"
    JSON_EXT = ".json"
    device_type = ""
    abbrev_dict = {}
    long_dict = {}

    def __init__(self, device_type):
        self.device_type = device_type
        with open(
            self.TEMPLATE_DIR + self.device_type + self.JSON_EXT, "r"
        ) as abbrev_json:
            self.abbrev_dict = json.load(abbrev_json)
            self.long_dict = {value: key for key, value in self.abbrev_dict.items()}

    def to_long(self, abbrev_intf):
        abbrev_key = max([key for key in self.abbrev_dict.keys() if key in abbrev_intf])
        return abbrev_intf.replace(abbrev_key, self.abbrev_dict[abbrev_key])

    def to_abbrev(self, long_intf):
        long_key = max([key for key in self.long_dict.keys() if key in long_intf])
        return long_intf.replace(long_key, self.long_dict[long_key])

    def normalization(self, intf_name):
        if self.is_abbrev(intf_name):
            return self.to_long(intf_name)
        else:
            return intf_name

    def is_abbrev(self, intf_name):
        base_intf = re.search(r'(?i)[a-z]+', intf_name).group()
        for key in self.abbrev_dict.keys():
            if base_intf == key:
                return True

        return False
