import json
import os
import re
from logging import getLogger

logger = getLogger(__name__)

# Template paths already reported as missing, so the warning is logged once per path
# instead of once per converter (a converter is created for every imported field).
_missing_template_paths = set()


class IntfAbbrevConverter:
    TEMPLATE_DIR = os.path.dirname(__file__) + "/templates/"
    SUFFIX = ".json"
    device_type = ""
    abbrev_to_long = {}
    long_to_abbrev = {}

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
                self.abbrev_to_long = json.load(abbrev_json)
                self.long_to_abbrev = {value: key for key, value in self.abbrev_to_long.items()}
        except FileNotFoundError:
            if template_file_path not in _missing_template_paths:
                _missing_template_paths.add(template_file_path)
                # A device type without a template is expected (callers fall back to no conversion).
                logger.warning(
                    f"Interface abbrev template file '{template_file_path}' not found"
                )
            raise

    @staticmethod
    def _convert_by_longest_prefix(intf_name: str, conversion_table: dict) -> str:
        """
        Convert the interface name using the longest key of the conversion table that it starts with.

        Returns the interface name unchanged if no key matches.
        """
        matched_keys = [key for key in conversion_table if intf_name.startswith(key)]
        if not matched_keys:
            return intf_name
        longest_key = max(matched_keys, key=len)
        return conversion_table[longest_key] + intf_name[len(longest_key):]

    def to_long(self, abbrev_intf: str) -> str:
        """
        Converts an abbreviated interface name to its long style.

        Args:
            abbrev_intf (str): The abbreviated interface name.

        Returns:
            str: The long style of the interface name, or the input if it has no known abbreviation.
        """
        return self._convert_by_longest_prefix(abbrev_intf, self.abbrev_to_long)

    def to_abbrev(self, long_intf: str) -> str:
        """
        Converts a long interface name to its abbreviated style.

        Args:
            long_intf (str): The long interface name.

        Returns:
            str: The abbreviated style of the interface name, or the input if it has no known long style.
        """
        return self._convert_by_longest_prefix(long_intf, self.long_to_abbrev)

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

    def find_unexpanded(self, intf_names) -> list:
        """
        List names that still look abbreviated after normalization.

        A normalized name that starts with a capital letter, up to two more letters and then a
        digit (for example "Di1") is probably a short form this device type's template does not
        list. Lower-case names such as "nve1" or "eth0" are native names, not Cisco-style
        abbreviations, and are not reported. The result is a list to review, not proof of a gap.

        Args:
            intf_names: Normalized interface names.

        Returns:
            list: The suspicious names, sorted.
        """
        return sorted(name for name in intf_names if re.match(r"[A-Z][A-Za-z]{0,2}\d", name))

    def is_abbrev(self, intf_name: str) -> bool:
        """
        Checks if the given interface name is abbreviated.

        Args:
            intf_name (str): The interface name.

        Returns:
            bool: True if the interface name is abbreviated, False otherwise.
        """
        base_match = re.search(r"(?i)[a-z]+", intf_name)
        if base_match is None:
            return False
        return base_match.group() in self.abbrev_to_long
