"""DLMS/COSEM CLI 参数解析

支持环境变量和命令行参数，命令行优先。
"""
import argparse
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConnectionArgs:
    """运行时连接参数"""
    # 传输层
    protocol: str = "hdlc"           # hdlc | wpdu | tcp
    transport: str = "serial"        # serial | tcp

    # 串口参数
    port: str = ""                   # /dev/ttyUSB0, COM3, etc.
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "none"             # none | even | odd
    stopbits: int = 1

    # TCP 参数
    server_ip: str = ""
    server_port: int = 4059
    client_id: str = ""

    # HDLC 参数
    client_logical_address: int = 16  # (0x10)
    server_logical_address: int = 1
    client_physical_address: int = 0
    server_physical_address: int = 0
    hdlc_max_info_receive: int = 128
    hdlc_window_size: int = 1

    # WPDU 参数
    wpdu_timeout: int = 60

    # DLMS 应用层
    client_system_title: str = ""    # hex string
    authentication: str = "none"     # none | lls | hls_gmac | hls_sha256
    security_suite: int = 0
    global_encryption_key: str = ""  # hex string
    global_authentication_key: str = ""  # hex string
    lls_password: str = ""           # hex string

    # 通用
    timeout: int = 10
    retries: int = 3
    verbose: bool = False


def from_env() -> dict:
    """从环境变量读取配置，前缀 DLMS_"""
    def _env(name: str, default: str = "") -> str:
        return os.environ.get(f"DLMS_{name}", default)

    def _env_int(name: str, default: int = 0) -> int:
        val = _env(name)
        return int(val) if val else default

    def _env_bool(name: str, default: bool = False) -> bool:
        val = _env(name)
        if val:
            return val.lower() in ("1", "true", "yes")
        return default

    return {
        "protocol": _env("PROTOCOL", "hdlc"),
        "transport": _env("TRANSPORT", "serial"),
        "port": _env("PORT"),
        "baudrate": _env_int("BAUDRATE", 9600),
        "bytesize": _env_int("BYTESIZE", 8),
        "parity": _env("PARITY", "none"),
        "stopbits": _env_int("STOPBITS", 1),
        "server_ip": _env("SERVER_IP"),
        "server_port": _env_int("SERVER_PORT", 4059),
        "client_id": _env("CLIENT_ID"),
        "client_logical_address": _env_int("CLIENT_LOGICAL_ADDRESS", 16),
        "server_logical_address": _env_int("SERVER_LOGICAL_ADDRESS", 1),
        "client_physical_address": _env_int("CLIENT_PHYSICAL_ADDRESS", 0),
        "server_physical_address": _env_int("SERVER_PHYSICAL_ADDRESS", 0),
        "hdlc_max_info_receive": _env_int("HDLC_MAX_INFO_RECEIVE", 128),
        "hdlc_window_size": _env_int("HDLC_WINDOW_SIZE", 1),
        "wpdu_timeout": _env_int("WPDU_TIMEOUT", 60),
        "client_system_title": _env("CLIENT_SYSTEM_TITLE"),
        "authentication": _env("AUTHENTICATION", "none"),
        "security_suite": _env_int("SECURITY_SUITE", 0),
        "global_encryption_key": _env("GLOBAL_ENCRYPTION_KEY"),
        "global_authentication_key": _env("GLOBAL_AUTHENTICATION_KEY"),
        "lls_password": _env("LLS_PASSWORD"),
        "timeout": _env_int("TIMEOUT", 10),
        "retries": _env_int("RETRIES", 3),
        "verbose": _env_bool("VERBOSE", False),
    }


def parse_args(argv=None) -> ConnectionArgs:
    """解析命令行参数，支持环境变量回退"""
    env = from_env()

    parser = argparse.ArgumentParser(
        description="DLMS/COSEM 连接参数配置",
    )

    # 传输层
    parser.add_argument("--protocol", default=env["protocol"],
                        choices=["hdlc", "wpdu", "tcp"],
                        help="协议层 (default: %(default)s)")
    parser.add_argument("--transport", default=env["transport"],
                        choices=["serial", "tcp"],
                        help="传输方式 (default: %(default)s)")

    # 串口参数
    parser.add_argument("--port", default=env["port"],
                        help="串口设备路径 (e.g. /dev/ttyUSB0)")
    parser.add_argument("--baudrate", type=int, default=env["baudrate"],
                        help="波特率 (default: %(default)s)")
    parser.add_argument("--parity", default=env["parity"],
                        choices=["none", "even", "odd"],
                        help="校验 (default: %(default)s)")

    # TCP 参数
    parser.add_argument("--server-ip", default=env["server_ip"],
                        help="TCP 服务器 IP")
    parser.add_argument("--server-port", type=int, default=env["server_port"],
                        help="TCP 端口 (default: %(default)s)")
    parser.add_argument("--client-id", default=env["client_id"],
                        help="GPRS Client ID")

    # HDLC 参数
    parser.add_argument("--client-logical-address", type=int,
                        default=env["client_logical_address"],
                        help="客户端逻辑地址 (default: %(default)s)")
    parser.add_argument("--server-logical-address", type=int,
                        default=env["server_logical_address"],
                        help="服务器逻辑地址 (default: %(default)s)")
    parser.add_argument("--client-physical-address", type=int,
                        default=env["client_physical_address"],
                        help="客户端物理地址 (default: %(default)s)")
    parser.add_argument("--server-physical-address", type=int,
                        default=env["server_physical_address"],
                        help="服务器物理地址 (default: %(default)s)")
    parser.add_argument("--hdlc-max-info-receive", type=int,
                        default=env["hdlc_max_info_receive"],
                        help="HDLC 最大接收信息长度 (default: %(default)s)")
    parser.add_argument("--hdlc-window-size", type=int,
                        default=env["hdlc_window_size"],
                        help="HDLC 窗口大小 (default: %(default)s)")

    # WPDU 参数
    parser.add_argument("--wpdu-timeout", type=int,
                        default=env["wpdu_timeout"],
                        help="WPDU 超时秒数 (default: %(default)s)")

    # DLMS 应用层
    parser.add_argument("--client-system-title", default=env["client_system_title"],
                        help="客户端系统标题 (hex)")
    parser.add_argument("--authentication", default=env["authentication"],
                        choices=["none", "lls", "hls_gmac", "hls_sha256"],
                        help="认证方式 (default: %(default)s)")
    parser.add_argument("--security-suite", type=int,
                        default=env["security_suite"],
                        help="安全套件编号 (default: %(default)s)")
    parser.add_argument("--global-encryption-key",
                        default=env["global_encryption_key"],
                        help="全局加密密钥 (hex)")
    parser.add_argument("--global-authentication-key",
                        default=env["global_authentication_key"],
                        help="全局认证密钥 (hex)")
    parser.add_argument("--lls-password", default=env["lls_password"],
                        help="LLS 密码 (hex)")

    # 通用
    parser.add_argument("--timeout", type=int, default=env["timeout"],
                        help="超时秒数 (default: %(default)s)")
    parser.add_argument("--retries", type=int, default=env["retries"],
                        help="重试次数 (default: %(default)s)")
    parser.add_argument("--verbose", action="store_true",
                        default=env["verbose"],
                        help="详细输出")

    args = parser.parse_args(argv)
    return ConnectionArgs(**vars(args))
