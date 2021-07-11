import json
import os


class ImportCommandMapper:
    MAPPING_DIR = os.path.dirname(__file__) + "/mappings/"
    device_type: str
    mapping_dict: dict
    SUFFIX = ".json"

    def __init__(self, device_type):
        self.device_type = device_type
        with open(
            self.MAPPING_DIR + self.device_type + self.SUFFIX, "r"
        ) as mapping_json:
            self.mapping_dict = json.load(mapping_json)
