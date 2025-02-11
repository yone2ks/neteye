import json
import os
from logging import getLogger
from typing import Callable

from neteye.lib.intf_abbrev.intf_abbrev import IntfAbbrevConverter
from neteye.lib.utils.neteye_normalizer import normalize_noop, normalize_mac_address, normalize_mask, normalize_speed, normalize_duplex
from neteye.serial.models import Serial
from neteye.interface.models import Interface
from neteye.arp_entry.models import ArpEntry
from neteye.node.models import Node

logger = getLogger(__name__)

# Import types
IMPORT_TYPES = {
    Serial: "import_serial",
    Node: "import_node",
    Interface: "import_interface",
    ArpEntry: "import_arp_entry"
}

class ImportCommandMapper:
    MAPPING_DIR = os.path.dirname(__file__) + "/mappings/"
    SUFFIX = ".json"

    def __init__(self, device_type: str) -> None:
        """
        Initialize ImportCommandMapper.

        Args:
            device_type (str): The device type.

        Raises:
            FileNotFoundError: If the mapping file is not found.

        Returns:
            None
        """
        self.device_type = device_type
        self.mapping_dict = self._load_mapping()


    def _load_mapping(self) -> dict:
        mapping_file_path = os.path.join(self.MAPPING_DIR, f"{self.device_type}{self.SUFFIX}")
        try:
            with open(mapping_file_path, "r") as mapping_json:
                return json.load(mapping_json)
        except FileNotFoundError:
            logger.error(f"Import command mapping file '{mapping_file_path}' not found")
            raise


    def get_mappings(self, import_type: str) -> list:
        """
        Get the mappings by type.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.

        Returns:
            list: The mappings.
        """
        return self.mapping_dict.get(import_type, [])


    def get_commands(self, import_type: str) -> list:
        """
        Get the commands by type.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.

        Returns:
            list: The commands.
        """
        return [mapping["command"] for mapping in self.get_mappings(import_type)]


    def get_command(self, import_type: str, command: str) -> dict:
        """
        Get the command by type and command.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.
            command (str): The command.

        Returns:
            dict: The command.
        """
        mappings = self.get_mappings(import_type)
        for mapping in mappings:
            if mapping["command"] == command:
                return mapping
        return {}


    def get_fields(self, import_type: str, command: str) -> dict:
        """
        Get the fields by type and command.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.
            command (str): The command.

        Returns:
            dict: The fields.
        """
        mappings = self.get_mappings(import_type)
        for mapping in mappings:
            if mapping["command"] == command:
                return mapping["field"]
        return {}


    def get_source(self, import_type: str, command: str, field: str) -> str:
        """
        Get the source by type, command, and field.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.
            command (str): The command.
            field (str): The field.

        Returns:
            str: The source.
        """
        return self.get_fields(import_type, command).get(field, "").get("source")


    def get_normalizer(self, import_type: str, command: str, field: str) -> Callable:
        """
        Get the normalizer by type, command, and field.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.
            command (str): The command.
            field (str): The field.

        Returns:
            Callable: The normalizer.
        """
        normalizer_mapping = {
            "noop": normalize_noop,
            "interface": IntfAbbrevConverter(self.device_type).normalization,
            "mac_address": normalize_mac_address,
            "mask": normalize_mask,
            "speed": normalize_speed,
            "duplex": normalize_duplex
        }
        normalizer_type = self.get_fields(import_type, command).get(field, "").get("normalizer", "noop")
        return normalizer_mapping.get(normalizer_type, normalize_noop)


    def get_value_from_record(self, import_type: str, command: str, field: str, record: dict) -> str:
        """
        Get the record value by type, command, field, and record.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.
            command (str): The command.
            field (str): The field.
            record (dict): The record.
        
        Returns:
            str: The record value.
        """
        source = self.get_source(import_type, command, field)
        normalizer = self.get_normalizer(import_type, command, field)
        return normalizer(record.get(source, ""))


    def get_index(self, import_type: str, command: str) -> int:
        """
        Get the index by type and command.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.
            command (str): The command.

        Returns:
            int: The index, or None if not found.
        """
        return self.get_command(import_type, command).get("index", None)


    def get_ignore(self, import_type: str, command: str) -> list:
        """
        Get the ignore by type and command.

        Args:
            import_type (str): The import type. One of the values in IMPORT_TYPES.
            command (str): The command.

        Returns:
            list: The ignore.
        """
        return self.get_command(import_type, command).get("ignore", [])


    def filter_ignore_records(self, import_type: str, command: str, result: list) -> list:
        """
        Filter out ignore records from the result.

        Args:
            import_command (dict): The import command.
            result (list): The result.

        Returns:
            list: The filtered result.
        """
        ignore_conditions = self.get_ignore(import_type, command)
        filtered_result = []
        for record in result:
            is_ignored = any(
                all(record.get(key) == value for key, value in condition.items())
                for condition in ignore_conditions
            )
            if not is_ignored:
                filtered_result.append(record)
        return filtered_result