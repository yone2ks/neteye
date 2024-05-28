import json
import os
import re
from logging import getLogger

logger = getLogger(__name__)


class IntfAbbrevConverter:
    TEMPLATE_DIR = os.path.dirname(__file__) + "/templates/"
    SUFFIX = ".json"
    device_type = ""
    abbrev_dict = {}
    long_dict = {}

    def __init__(self, device_type: str) -> None:
        """
        Initializes the IntfAbbrevConverter object.

        Args:
            device_type (str): The type of device.

        Raises:
            FileNotFoundError: If the interface abbrev template file is not found.

        Returns:
            None
        """
        self.device_type = device_type
        template_file_path = f"{self.TEMPLATE_DIR}{self.device_type}{self.SUFFIX}"
        try:
            with open(template_file_path, "r") as abbrev_json:
                self.abbrev_dict = json.load(abbrev_json)
                self.long_dict = {value: key for key, value in self.abbrev_dict.items()}
        except FileNotFoundError:
            logger.error(
                f"Interface abbrev template file '{template_file_path}' not found"
            )
            raise

    def to_long(self, abbrev_intf: str) -> str:
        """
        Converts an abbreviated interface name to its long style.

        Args:
            abbrev_intf (str): The abbreviated interface name.

        Returns:
            str: The long style of the interface name.
        """
        abbrev_key = max([key for key in self.abbrev_dict.keys() if key in abbrev_intf])
        return abbrev_intf.replace(abbrev_key, self.abbrev_dict[abbrev_key])

    def to_abbrev(self, long_intf: str) -> str:
        """
        Converts a long interface name to its abbreviated style.

        Args:
            long_intf (str): The long interface name.

        Returns:
            str: The abbreviated style of the interface name.
        """
        long_key = max([key for key in self.long_dict.keys() if key in long_intf])
        return long_intf.replace(long_key, self.long_dict[long_key])

    def normalization(self, intf_name: str) -> str:
        """
        Normalize the interface name to long style if it is abbreviated.

        Args:
            intf_name (str): The interface name.

        Returns:
            str: The long style of the interface name if it is abbreviated, otherwise the original interface name.
        """
        if self.is_abbrev(intf_name):
            return self.to_long(intf_name)
        else:
            return intf_name

    def is_abbrev(self, intf_name: str) -> bool:
        """
        Checks if the given interface name is abbreviated.

        Args:
            intf_name (str): The interface name.

        Returns:
            bool: True if the interface name is abbreviated, False otherwise.
        """
        base_intf = re.search(r"(?i)[a-z]+", intf_name).group()
        for key in self.abbrev_dict.keys():
            if base_intf == key:
                return True

        return False
