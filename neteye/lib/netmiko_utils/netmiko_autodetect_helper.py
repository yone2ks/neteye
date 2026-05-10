import threading

import netmiko
from netmiko import ssh_autodetect
from netmiko.ssh_autodetect import SSHDetect
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# SSH_MAPPER_BASE はモジュールレベルのグローバル変数であるため、
# 複数スレッドが同時に autodetect を実行すると競合が発生する。
# このロックで「フィルタ置換 → autodetect() 実行 → 復元」を排他制御する。
_mapper_lock = threading.Lock()


def detect_device_type(node, specified_device_types: Optional[List[str]] = None):
    """
    SSH_MAPPER_BASE をフィルタリングして高速デバイスタイプ検出を実現する。

    SSHDetect の初期化（SSH 接続確立）はロック外で行い、
    autodetect() 呼び出しの直前だけロックを取得することで、
    スレッド競合を防ぎつつ並列 SSH 接続を許容する。

    Args:
        node: Node オブジェクト
        specified_device_types: 検出対象とするデバイスタイプのリスト。
                                None の場合は通常の自動検出を実行。

    Returns:
        str: 検出されたデバイスタイプ
    """
    params = node.gen_netmiko_params()
    params['device_type'] = 'autodetect'

    try:
        # SSH 接続確立はロック外（遅い処理を並列化するため）
        detector = SSHDetect(**params)

        if specified_device_types:
            # autodetect() が参照するモジュールレベル変数の置換をロックで保護
            with _mapper_lock:
                original_mapper = ssh_autodetect.SSH_MAPPER_BASE
                specified_mapper = [
                    (device_type, autodetect_dict)
                    for device_type, autodetect_dict in original_mapper
                    if device_type in specified_device_types
                ]
                ssh_autodetect.SSH_MAPPER_BASE = specified_mapper
                try:
                    detected_type = detector.autodetect()
                finally:
                    ssh_autodetect.SSH_MAPPER_BASE = original_mapper
        else:
            detected_type = detector.autodetect()

        if detected_type:
            return detected_type
        else:
            logger.warning(
                f"Could not detect device type for {node.ip_address}, "
                "falling back to cisco_ios_telnet"
            )
            return "cisco_ios_telnet"

    except netmiko.exceptions.NetMikoAuthenticationException as err:
        # Re-raise authentication failures so callers (e.g. try_connect_node)
        # can cycle through credentials instead of falling back to telnet.
        logger.error(f"SSH detection failed for {node.ip_address}: {err}")
        raise
    except (
        netmiko.exceptions.NetMikoTimeoutException,
        netmiko.exceptions.SSHException,
    ) as err:
        logger.error(f"SSH detection failed for {node.ip_address}: {err}")
        return "cisco_ios_telnet"
