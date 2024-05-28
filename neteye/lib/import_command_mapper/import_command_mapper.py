import json
import os
from logging import getLogger

logger = getLogger(__name__)


class ImportCommandMapper:
    MAPPING_DIR = os.path.dirname(__file__) + "/mappings/"
    device_type: str
    mapping_dict: dict
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
        mapping_file_path = os.path.join(
            self.MAPPING_DIR, f"{self.device_type}{self.SUFFIX}"
        )
        if not os.path.isfile(mapping_file_path):
            logger.error(f"Import command mapping file '{mapping_file_path}' not found")
            raise FileNotFoundError(
                f"Import command mapping file '{mapping_file_path}' not found"
            )
        with open(mapping_file_path, "r") as mapping_json:
            self.mapping_dict = json.load(mapping_json)
