from dynaconf import Validator

# Centralized defaults for timeouts/keepalive.
DEFAULTS = {
    # Netmiko
    "NETMIKO_READ_TIMEOUT": 10,
    "NETMIKO_CONN_TIMEOUT": 5,
    "NETMIKO_AUTH_TIMEOUT": 5,
    "NETMIKO_BANNER_TIMEOUT": 5,
    "NETMIKO_KEEPALIVE": 10,
    # Scrapli
    "SCRAPLI_TIMEOUT_SOCKET": 10,
    "SCRAPLI_TIMEOUT_TRANSPORT": 10,
    "SCRAPLI_TIMEOUT_OPS": 10,
    # Napalm
    "NAPALM_TIMEOUT": 10,
}

validators = [
    # Netmiko
    Validator("NETMIKO_READ_TIMEOUT", is_type_of=int, gt=0, default=DEFAULTS["NETMIKO_READ_TIMEOUT"]),
    Validator("NETMIKO_CONN_TIMEOUT", is_type_of=int, gt=0, default=DEFAULTS["NETMIKO_CONN_TIMEOUT"]),
    Validator("NETMIKO_AUTH_TIMEOUT", is_type_of=int, gt=0, default=DEFAULTS["NETMIKO_AUTH_TIMEOUT"]),
    Validator("NETMIKO_BANNER_TIMEOUT", is_type_of=int, gt=0, default=DEFAULTS["NETMIKO_BANNER_TIMEOUT"]),
    Validator("NETMIKO_KEEPALIVE", is_type_of=int, gte=0, default=DEFAULTS["NETMIKO_KEEPALIVE"]),
    # Scrapli
    Validator("SCRAPLI_TIMEOUT_SOCKET", is_type_of=int, gt=0, default=DEFAULTS["SCRAPLI_TIMEOUT_SOCKET"]),
    Validator("SCRAPLI_TIMEOUT_TRANSPORT", is_type_of=int, gt=0, default=DEFAULTS["SCRAPLI_TIMEOUT_TRANSPORT"]),
    Validator("SCRAPLI_TIMEOUT_OPS", is_type_of=int, gt=0, default=DEFAULTS["SCRAPLI_TIMEOUT_OPS"]),
    # Napalm
    Validator("NAPALM_TIMEOUT", is_type_of=int, gt=0, default=DEFAULTS["NAPALM_TIMEOUT"]),
    # Autodetect
    Validator("AUTO_DETECT_DEVICE_TYPES", is_type_of=list, default=[]),
]
