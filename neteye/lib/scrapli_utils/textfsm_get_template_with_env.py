from logging import getLogger
from netmiko.utilities import get_template_dir
from textfsm.clitable import CliTable

logger = getLogger(__name__)

def textfsm_get_template_with_env(platform: str, command: str) -> str:
    """
    Get TextFSM template with environment variables(NET_TEXTFSM).
    scrapli does not support specifying the template directory using NET_TEXTFSM.
    (netmiko support NET_TEXTFSM.)
    This method also helps scrapli to support NET_TEXTFSM, and 

    Args:
        platform (str): The platform of the device.
        command (str): The command to parse.

    Returns:
        str: The path to the TextFSM template.
    """
    template_dir = get_template_dir()
    cli_table = CliTable("index", template_dir)
    template_index = cli_table.index.GetRowMatch({"Platform": platform, "Command": command})
    if not template_index:
        logger.warning(
            f"No match in ntc_templates index for platform `{platform}` and command `{command}`"
        )
        return None
    template_name = cli_table.index.index[template_index]["Template"]
    return f"{template_dir}/{template_name}"

