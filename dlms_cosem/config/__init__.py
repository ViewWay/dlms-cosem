"""DLMS/COSEM Configuration Module.

Provides utilities for loading and managing meter connection configurations
from YAML files and environment variables.

Example usage:
    from dlms_cosem.config import load_meter_config, get_connection_settings

    # Load config
    config = load_meter_config()

    # Get connection settings for a meter
    settings = get_connection_settings(config, meter_id="meter_001")

    # Or use default settings
    settings = get_connection_settings(config)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Dict
from pathlib import Path

if TYPE_CHECKING:
    from dlms_cosem import DlmsConnectionSettings

__all__ = [
    # YAML配置
    "MeterConfig",
    "SecurityConfig",
    "ConnectionConfig",
    "load_meter_config",
    "get_connection_settings",
    "get_meter_config",
    # 环境变量配置
    "load_env",
    "get_env_settings",
    "list_env_meters",
    # CLI 参数
    "ConnectionArgs",
    # 分层配置 (Basic, Key, HDLC, WPDU, AARQ)
    "load_layered_config",
    "LayeredConfig",
    "BasicConfig",
    "KeyConfig",
    "HdlcConfig",
    "WpduConfig",
    "AarqConfig",
]


# 环境变量配置支持
def load_env(path: Optional[str] = None) -> bool:
    """加载 .env 文件

    Args:
        path: .env 文件路径

    Returns:
        是否成功加载
    """
    from dlms_cosem.config.env_config import load_env as _load_env
    return _load_env(path)


def get_env_settings(
    meter_id: Optional[str] = None,
) -> "DlmsConnectionSettings":
    """从环境变量获取连接设置

    Args:
        meter_id: 电表ID，如 "001" (对应 METER_001_*)

    Returns:
        DLMS连接设置对象
    """
    from dlms_cosem.config.env_config import get_connection_settings
    return get_connection_settings(meter_id=meter_id)


def list_env_meters() -> list[str]:
    """列出环境变量中配置的电表ID

    Returns:
        电表ID列表
    """
    from dlms_cosem.config.env_config import list_meter_ids
    return list_meter_ids()


@dataclass
class SecurityConfig:
    """安全配置"""

    level: str = "hls"  # public, low, hls
    suite: str = "HLS_GMAC"  # HLS_ISM, HLS_GMAC, SM4_GMAC, SM4_GCM
    authentication_key: str = ""
    encryption_key: str = ""
    client_system_title: str = ""
    password: str = "00000000"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityConfig":
        """从字典创建安全配置"""
        keys = data.get("keys", {})
        return cls(
            level=data.get("level", "hls"),
            suite=data.get("suite", "HLS_GMAC"),
            authentication_key=keys.get("authentication", ""),
            encryption_key=keys.get("encryption", ""),
            client_system_title=keys.get("client_system_title", ""),
            password=keys.get("password", "00000000"),
        )


@dataclass
class ConnectionConfig:
    """连接配置"""

    host: str = "localhost"
    port: int = 4059
    client_logical_address: int = 16
    server_logical_address: int = 1
    timeout: int = 10
    retries: int = 3
    keepalive: bool = True
    security: Optional[SecurityConfig] = None

    def __post_init__(self):
        if self.security is None:
            self.security = SecurityConfig()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionConfig":
        """从字典创建连接配置"""
        security_data = data.get("security")
        security = SecurityConfig.from_dict(security_data) if security_data else SecurityConfig()

        return cls(
            host=data.get("host", "localhost"),
            port=data.get("port", 4059),
            client_logical_address=data.get("client_logical_address", 16),
            server_logical_address=data.get("server_logical_address", 1),
            timeout=data.get("timeout", 10),
            retries=data.get("retries", 3),
            keepalive=data.get("keepalive", True),
            security=security,
        )


@dataclass
class MeterConfig:
    """电表配置"""

    name: str = "default"
    connection: Optional[ConnectionConfig] = None
    profile: str = ""

    def __post_init__(self):
        if self.connection is None:
            self.connection = ConnectionConfig()

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any], profiles: Dict[str, Any]) -> "MeterConfig":
        """从字典创建电表配置"""
        conn_data = {k: v for k, v in data.items() if k != "profile"}

        # 如果指定了profile，合并配置
        profile_name = data.get("profile", "")
        if profile_name and profile_name in profiles:
            profile_data = profiles[profile_name]
            if "security" in profile_data:
                if "security" not in conn_data:
                    conn_data["security"] = {}
                conn_data["security"].update(profile_data["security"])

        return cls(
            name=name,
            connection=ConnectionConfig.from_dict(conn_data),
            profile=profile_name,
        )


def load_yaml_config(path: Optional[str] = None) -> Dict[str, Any]:
    """加载YAML配置文件

    Args:
        path: 配置文件路径，默认查找以下位置:
              - ./meter_config.local.yaml
              - ./config/meter_config.yaml
              - ~/.dlms_cosem/meter_config.yaml

    Returns:
        配置字典
    """
    import yaml

    search_paths = []
    if path:
        search_paths.append(Path(path))
    else:
        search_paths.extend([
            Path.cwd() / "meter_config.local.yaml",
            Path.cwd() / "config" / "meter_config.yaml",
            Path.home() / ".dlms_cosem" / "meter_config.yaml",
        ])

    for config_path in search_paths:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)

    # 返回默认配置
    return _get_default_config()


def _get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "default": {
            "host": "localhost",
            "port": 4059,
            "client_logical_address": 16,
            "server_logical_address": 1,
            "timeout": 10,
            "retries": 3,
            "security": {
                "level": "hls",
                "suite": "HLS_GMAC",
                "keys": {
                    "authentication": "",
                    "encryption": "",
                    "client_system_title": "",
                }
            }
        },
        "profiles": {},
        "meters": {},
    }


class MeterConfigManager:
    """电表配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self._config = load_yaml_config(config_path)
        self._profiles = self._config.get("profiles", {})
        self._meters = self._config.get("meters", {})
        self._default = self._config.get("default", {})

    def get_meter(self, meter_id: str) -> MeterConfig:
        """获取指定电表配置

        Args:
            meter_id: 电表ID (如 "meter_001")

        Returns:
            电表配置
        """
        if meter_id in self._meters:
            return MeterConfig.from_dict(
                meter_id,
                self._meters[meter_id],
                self._profiles,
            )

        # 如果找不到，返回默认配置
        return MeterConfig.from_dict(
            meter_id,
            self._default,
            self._profiles,
        )

    def get_default(self) -> ConnectionConfig:
        """获取默认连接配置"""
        return ConnectionConfig.from_dict(self._default)

    def get_profile(self, profile_name: str) -> ConnectionConfig:
        """获取预设配置"""
        if profile_name in self._profiles:
            return ConnectionConfig.from_dict(self._profiles[profile_name])
        raise ValueError(f"Profile '{profile_name}' not found")

    def list_meters(self) -> list[str]:
        """列出所有已配置的电表"""
        return list(self._meters.keys())

    def list_profiles(self) -> list[str]:
        """列出所有预设配置"""
        return list(self._profiles.keys())


# 全局配置管理器实例
_config_manager: Optional[MeterConfigManager] = None


def load_meter_config(config_path: Optional[str] = None) -> MeterConfigManager:
    """加载电表配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置管理器实例
    """
    global _config_manager
    _config_manager = MeterConfigManager(config_path)
    return _config_manager


def get_connection_settings(
    config: Optional[MeterConfigManager] = None,
    meter_id: Optional[str] = None,
    profile: Optional[str] = None,
    cli_args: Optional[ConnectionArgs] = None,
) -> "DlmsConnectionSettings":
    """获取连接设置

    Args:
        config: 配置管理器，默认使用全局实例
        meter_id: 电表ID
        profile: 预设配置名
        cli_args: CLI 参数对象，优先级最高

    Returns:
        DLMS连接设置对象
    """
    from dlms_cosem import DlmsConnectionSettings

    # CLI 参数优先
    if cli_args is not None:
        return _settings_from_cli_args(cli_args)

    if config is None:
        if _config_manager is None:
            config = load_meter_config()
        else:
            config = _config_manager

    # 获取配置
    if meter_id:
        meter_config = config.get_meter(meter_id)
        conn = meter_config.connection
    elif profile:
        conn = config.get_profile(profile)
    else:
        conn = config.get_default()

    security = conn.security
    if security is None:
        security = SecurityConfig()

    # 构建连接设置
    settings = DlmsConnectionSettings(
        client_logical_address=conn.client_logical_address,
        server_logical_address=conn.server_logical_address,
    )

    # 设置认证方式
    if security.level == "public":
        settings.authentication = "none"
    elif security.level == "low":
        settings.authentication = "low"
        settings.password = security.password.encode("ascii")
    elif security.level == "hls":
        settings.authentication = "hls"

        # 设置密钥
        if security.authentication_key:
            settings.authentication_key = bytes.fromhex(security.authentication_key)
        if security.encryption_key:
            settings.encryption_key = bytes.fromhex(security.encryption_key)
        if security.client_system_title:
            settings.client_system_title = bytes.fromhex(security.client_system_title)

    return settings


def get_meter_config(meter_id: str, config_path: Optional[str] = None) -> MeterConfig:
    """获取电表配置

    Args:
        meter_id: 电表ID
        config_path: 配置文件路径

    Returns:
        电表配置对象
    """
    manager = load_meter_config(config_path)
    return manager.get_meter(meter_id)


# 便捷函数
def _settings_from_cli_args(cli_args: ConnectionArgs) -> DlmsConnectionSettings:
    """从 ConnectionArgs 创建 DlmsConnectionSettings"""
    from dlms_cosem import DlmsConnectionSettings

    settings = DlmsConnectionSettings(
        client_logical_address=cli_args.client_logical_address,
        server_logical_address=cli_args.server_logical_address,
    )

    # 认证
    auth = cli_args.authentication
    if auth == "none":
        settings.authentication = "none"
    elif auth == "lls":
        settings.authentication = "low"
        if cli_args.lls_password:
            settings.password = bytes.fromhex(cli_args.lls_password)
    elif auth in ("hls_gmac", "hls_sha256"):
        settings.authentication = "hls"
        if cli_args.global_encryption_key:
            settings.encryption_key = bytes.fromhex(cli_args.global_encryption_key)
        if cli_args.global_authentication_key:
            settings.authentication_key = bytes.fromhex(cli_args.global_authentication_key)
        if cli_args.client_system_title:
            settings.client_system_title = bytes.fromhex(cli_args.client_system_title)

    return settings


def quick_connect(
    host: str,
    port: int = 4059,
    client_address: int = 16,
    server_address: int = 1,
    security: str = "hls",
    akey: str = "",
    ekey: str = "",
) -> "DlmsConnectionSettings":
    """快速创建连接设置

    Args:
        host: 电表IP地址
        port: 端口号
        client_address: 客户端逻辑地址
        server_address: 服务器逻辑地址
        security: 安全级别 (public, low, hls)
        akey: 认证密钥(十六进制)
        ekey: 加密密钥(十六进制)

    Returns:
        DLMS连接设置对象
    """
    from dlms_cosem import DlmsConnectionSettings

    settings = DlmsConnectionSettings(
        client_logical_address=client_address,
        server_logical_address=server_address,
    )

    if security == "public":
        settings.authentication = "none"
    elif security == "low":
        settings.authentication = "low"
        settings.password = b"00000000"
    elif security == "hls":
        settings.authentication = "hls"
        if akey:
            settings.authentication_key = bytes.fromhex(akey)
        if ekey:
            settings.encryption_key = bytes.fromhex(ekey)

    return settings


# 分层配置支持
def load_layered_config(config_path: Optional[str] = None):
    """加载分层配置

    按照DLMS/COSEM协议栈层次组织:
    - Basic:   基础配置
    - Key:     密钥配置
    - HDLC:    数据链路层配置
    - WPDU:    传输层配置 (TCP/IP)
    - AARQ:    应用层配置 (认证/加密)

    Args:
        config_path: 配置文件路径

    Returns:
        LayeredConfig对象
    """
    from dlms_cosem.config.layered_config import load_layered_config as _load
    return _load(config_path)


# 导出分层配置类
from dlms_cosem.config.layered_config import (
    LayeredConfig,
    BasicConfig,
    KeyConfig,
    HdlcConfig,
    WpduConfig,
    AarqConfig,
)
from dlms_cosem.cli_args import ConnectionArgs


__getattr__ = __all__
