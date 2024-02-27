""" import scrapli_community==23.7.30 """
from scrapli_community.aethra.atosnt import aethra_atosnt
from scrapli_community.alcatel.aos import alcatel_aos
from scrapli_community.aruba.aoscx import aruba_aoscx
from scrapli_community.cisco.aireos import cisco_aireos
from scrapli_community.cisco.asa import cisco_asa
from scrapli_community.cisco.cbs import cisco_cbs
from scrapli_community.cumulus.linux import cumulus_linux
from scrapli_community.cumulus.vtysh import cumulus_vtysh
from scrapli_community.dlink.os import dlink_os
from scrapli_community.edgecore.ecs import edgecore_ecs
from scrapli_community.eltex.esr import eltex_esr
from scrapli_community.fortinet.fortios import fortinet_fortios
from scrapli_community.fortinet.wlc import fortinet_wlc
from scrapli_community.hp.comware import hp_comware
from scrapli_community.huawei.vrp import huawei_vrp
from scrapli_community.mikrotik.routeros import mikrotik_routeros
from scrapli_community.nokia.srlinux import nokia_srlinux
from scrapli_community.nokia.sros import nokia_sros
from scrapli_community.paloalto.panos import paloalto_panos
from scrapli_community.raisecom.ros import raisecom_ros
from scrapli_community.ruckus.fastiron import ruckus_fastiron
from scrapli_community.ruckus.unleashed import ruckus_unleashed
from scrapli_community.siemens.roxii import siemens_roxii
from scrapli_community.versa.flexvnf import versa_flexvnf
from scrapli_community.vyos.vyos import vyos

class ScrapliCommunityHelper:
    COMMUNITY_PLATFORM = {
        "aethra_atosnt": aethra_atosnt.SCRAPLI_PLATFORM,
        "alcatel_aos": alcatel_aos.SCRAPLI_PLATFORM,
        "aruba_aoscx": aruba_aoscx.SCRAPLI_PLATFORM,
        "cisco_aireos": cisco_aireos.SCRAPLI_PLATFORM,
        "cisco_asa": cisco_asa.SCRAPLI_PLATFORM,
        "cisco_cbs": cisco_cbs.SCRAPLI_PLATFORM,
        "cumulus_linux": cumulus_linux.SCRAPLI_PLATFORM,
        "cumulus_vtysh": cumulus_vtysh.SCRAPLI_PLATFORM,
        "dlink_os": dlink_os.SCRAPLI_PLATFORM,
        "edgecore_ecs": edgecore_ecs.SCRAPLI_PLATFORM,
        "eltex_esr": eltex_esr.SCRAPLI_PLATFORM,
        "fortinet_fortios": fortinet_fortios.SCRAPLI_PLATFORM,
        "fortinet_wlc": fortinet_wlc.SCRAPLI_PLATFORM,
        "hp_comware": hp_comware.SCRAPLI_PLATFORM,
        "huawei_vrp": huawei_vrp.SCRAPLI_PLATFORM,
        "mikrotik_routeros": mikrotik_routeros.SCRAPLI_PLATFORM,
        "nokia_srlinux": nokia_srlinux.SCRAPLI_PLATFORM,
        "nokia_sros": nokia_sros.SCRAPLI_PLATFORM,
        "paloalto_panos": paloalto_panos.SCRAPLI_PLATFORM,
        "raisecom_ros": raisecom_ros.SCRAPLI_PLATFORM,
        "ruckus_fastiron": ruckus_fastiron.SCRAPLI_PLATFORM,
        "ruckus_unleashed": ruckus_unleashed.SCRAPLI_PLATFORM,
        "siemens_roxii": siemens_roxii.SCRAPLI_PLATFORM,
        "versa_flexvnf": versa_flexvnf.SCRAPLI_PLATFORM,
        "vyos_vyos": vyos.SCRAPLI_PLATFORM,
    }

    @classmethod
    def is_community_platform(cls,  platform_name):
        return platform_name in cls.COMMUNITY_PLATFORM.keys()

    @classmethod
    def is_network_driver(cls, platform_name):
        return cls.COMMUNITY_PLATFORM[platform_name]["driver_type"] == "network"

    @classmethod
    def has_textfsm_platform_variable(cls, platform_name):
        return cls.is_community_platform(platform_name) and (not cls.is_network_driver(platform_name))
