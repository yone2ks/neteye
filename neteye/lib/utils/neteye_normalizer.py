import netaddr


def normalize_noop(value):
    """
    This is a no-op function that simply returns the given value unchanged.

    Args: 
        value (any): The value to normalize.

    Returns:
        any: The original value.
    """
    return value


def normalize_mac_address(mac_address, format=netaddr.mac_cisco):
    """
    Normalize the given MAC address.

    Args:
        mac_address (str): The MAC address to normalize.
        format (str): The format to use for the normalized MAC address. Default is netaddr.mac_cisco.

    Returns:
        str: The normalized MAC address.
    
    Note:
        - By default, the MAC address is represented in Cisco format (dot notation).
        - If the given MAC address is not valid, it is returned unchanged.
    """
    if netaddr.valid_mac(mac_address):
        return str(netaddr.EUI(mac_address).format(format))
    else:
        return mac_address

def normalize_mask(mask):
    """
    Normalize the given mask.

    If the mask is given as a dotted quad (e.g. "255.255.255.0"), it is converted to the corresponding CIDR prefix length (e.g., "24").
    Otherwise, the given mask is returned unchanged, assuming it is already in CIDR format.

    Args:
        mask (str): The mask to normalize.
    
    Returns:
        str: The normalized mask as a CIDR prefix length (e.g., 24). 
    """
    if "." in mask:
        return str(netaddr.IPAddress(mask).netmask_bits())  # Convert the dotted quad to CIDR prefix length (e.g., 24)
    else:
        return str(mask)  # Assume the mask is already in CIDR format (e.g., 24)

def normalize_speed(speed):
    """
    Normalize the given speed.

    Args:
        speed (str): The speed to normalize.

    Returns:
        str: The normalized speed.
    """
    speed_mapping = {
        "10": "10Mbps",
        "100": "100Mbps",
        "1000": "1Gbps",
        "10000": "10Gbps",
        "25000": "25Gbps",
        "40000": "40Gbps",
        "100000": "100Gbps"
    }
    normalized_speed = speed_mapping.get(speed, speed.replace(" ", "").lower())
    if "mbps" in normalized_speed:
        return normalized_speed.replace("mbps", "Mbps")
    if "gbps" in normalized_speed:
        return normalized_speed.replace("gbps", "Gbps")
    return normalized_speed

def normalize_duplex(duplex):
    """
    Normalize the given duplex.

    Args:
        duplex (str): The duplex to normalize.

    Returns:
        str: The normalized duplex in lowercase ('full' or 'half').
    """
    return duplex.strip().lower()

