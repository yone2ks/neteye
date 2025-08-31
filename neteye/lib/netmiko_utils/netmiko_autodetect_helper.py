import netmiko
from netmiko import ssh_autodetect
from netmiko.ssh_autodetect import SSHDetect
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def detect_device_type(node, specified_device_types: Optional[List[str]] = None):
    """
    SSH_MAPPER_BASEを一時的に置き換えて高速デバイスタイプ検出を実現する
    
    Args:
        node: Nodeオブジェクト
        specified_device_types: 検出対象とするデバイスタイプのリスト
                                Noneの場合は通常の自動検出を実行
    
    Returns:
        str: 検出されたデバイスタイプ
    """
    # 元のSSH_MAPPER_BASEをバックアップ
    original_mapper = ssh_autodetect.SSH_MAPPER_BASE.copy()
    
    try:
        # 指定されたデバイスタイプがある場合はフィルタ、なければそのまま使用
        if specified_device_types:
            specified_mapper = [(device_type, autodetect_dict) 
                                for device_type, autodetect_dict in original_mapper 
                                if device_type in specified_device_types]
            ssh_autodetect.SSH_MAPPER_BASE = specified_mapper
        
        params = node.gen_netmiko_params()
        params['device_type'] = 'autodetect'
        detector = SSHDetect(**params)
        detected_type = detector.autodetect()
        
        if detected_type:
            return detected_type
        else:
            logger.warning(f"Could not detect device type for {node.ip_address}, falling back to cisco_ios_telnet")
            return "cisco_ios_telnet"
            
    except (
        netmiko.exceptions.NetMikoTimeoutException,
        netmiko.exceptions.SSHException,
    ) as err:
        logger.error(f"SSH detection failed for {node.ip_address}: {err}")
        return "cisco_ios_telnet"
    finally:
        # SSH_MAPPER_BASEを元に戻す（指定されたデバイスタイプがある場合のみ）
        if specified_device_types:
            ssh_autodetect.SSH_MAPPER_BASE = original_mapper
