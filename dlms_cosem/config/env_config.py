"""Environment Variable Configuration Loader for DLMS/COSEM.

Provides utilities for loading meter connection configurations from .env files.

Example usage:
    from dlms_cosem.config.env_config import load_env, get_connection_settings

    # Load .env file
    load_env()

    # Get connection settings
    settings = get_connection_settings()

    # Or for specific meter
    settings = get_connection_settings(meter_id="METER_001")
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict

if TYPE_CHECKING:
    from dlms_cosem import DlmsConnectionSettings

# Try to import dotenv, provide fallback if not available
try:
    from dotenv import load_dotenv

    def _load_dotenv_file(path: Optional[str] = None) -> bool:
        """Load .env file using python-dotenv."""
        if path is None:
            # Search for .env file
            search_paths = [
                Path.cwd() / ".env",
                Path.cwd() / ".env.local",
                Path(__file__).parent.parent.parent / ".env",
            ]
            for env_path in search_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    return True
            return False
        else:
            return load_dotenv(path)

except ImportError:
    # Fallback: simple .env parser
    def _load_dotenv_file(path: Optional[str] = None) -> bool:
        """Simple .env file parser."""
        if path is None:
            search_paths = [
                Path.cwd() / ".env",
                Path.cwd() / ".env.local",
                Path(__file__).parent.parent.parent / ".env",
            ]
            for env_path in search_paths:
                if env_path.exists():
                    path = str(env_path)
                    break
            if path is None:
                return False

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Parse KEY=VALUE
                match = re.match(r"^(\w+)\s*=\s*(.+)$", line)
                if match:
                    key, value = match.groups()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ[key] = value
        return True


@dataclass
class MeterEnvConfig:
    """电表环境变量配置"""

    # Connection
    host: str = "localhost"
    port: int = 4059
    client_address: int = 16
    server_address: int = 1
    timeout: int = 10
    retries: int = 3

    # Security
    security_level: str = "hls"
    security_suite: str = "HLS_GMAC"
    auth_key: str = ""
    enc_key: str = ""
    client_system_title: str = ""
    password: str = "00000000"

    @classmethod
    def from_prefix(cls, prefix: str = "METER") -> "MeterEnvConfig":
        """从环境变量加载配置

        Args:
            prefix: 环境变量前缀，如 "METER" 或 "METER_001"
        """
        def get_env(key: str, default=""):
            return os.environ.get(f"{prefix}_{key}", default)

        def get_env_int(key: str, default: int = 0) -> int:
            val = os.environ.get(f"{prefix}_{key}", "")
            return int(val) if val else default

        return cls(
            host=get_env("HOST", "localhost"),
            port=get_env_int("PORT", 4059),
            client_address=get_env_int("CLIENT_ADDRESS", 16),
            server_address=get_env_int("SERVER_ADDRESS", 1),
            timeout=get_env_int("TIMEOUT", 10),
            retries=get_env_int("RETRIES", 3),
            security_level=get_env("SECURITY_LEVEL", "hls"),
            security_suite=get_env("SECURITY_SUITE", "HLS_GMAC"),
            auth_key=get_env("AUTH_KEY", get_env("AUTHENTICATION_KEY", "")),
            enc_key=get_env("ENC_KEY", get_env("ENCRYPTION_KEY", "")),
            client_system_title=get_env("CLIENT_SYSTEM_TITLE", ""),
            password=get_env("PASSWORD", get_env("LOW_LEVEL_PASSWORD", "00000000")),
        )


def load_env(path: Optional[str] = None) -> bool:
    """加载 .env 文件

    Args:
        path: .env 文件路径，默认搜索常用位置

    Returns:
        是否成功加载文件
    """
    return _load_dotenv_file(path)


def get_connection_settings(
    meter_id: Optional[str] = None,
    prefix: str = "METER",
) -> "DlmsConnectionSettings":
    """从环境变量获取连接设置

    Args:
        meter_id: 电表ID，如 "001" (对应 METER_001_*)
        prefix: 环境变量前缀

    Returns:
        DLMS连接设置对象
    """
    from dlms_cosem import DlmsConnectionSettings
    from dlms_cosem.cli_args import from_env as _cli_from_env

    # Build prefix
    env_prefix = f"{prefix}_{meter_id}" if meter_id else prefix
    config = MeterEnvConfig.from_prefix(env_prefix)

    # Create connection settings
    settings = DlmsConnectionSettings(
        client_logical_address=config.client_address,
        server_logical_address=config.server_address,
    )

    # Set authentication based on security level
    if config.security_level == "public":
        settings.authentication = "none"
    elif config.security_level == "low":
        settings.authentication = "low"
        settings.password = config.password.encode("ascii")
    elif config.security_level == "hls":
        settings.authentication = "hls"

        # Set keys if provided
        if config.auth_key:
            try:
                settings.authentication_key = bytes.fromhex(config.auth_key)
            except ValueError:
                raise ValueError(f"Invalid AUTH_KEY format: {config.auth_key}")

        if config.enc_key:
            try:
                settings.encryption_key = bytes.fromhex(config.enc_key)
            except ValueError:
                raise ValueError(f"Invalid ENC_KEY format: {config.enc_key}")

        if config.client_system_title:
            try:
                settings.client_system_title = bytes.fromhex(config.client_system_title)
            except ValueError:
                raise ValueError(f"Invalid CLIENT_SYSTEM_TITLE format: {config.client_system_title}")

    return settings


def get_meter_host(
    meter_id: Optional[str] = None,
    prefix: str = "METER",
) -> tuple[str, int]:
    """获取电表主机和端口

    Args:
        meter_id: 电表ID
        prefix: 环境变量前缀

    Returns:
        (host, port) 元组
    """
    env_prefix = f"{prefix}_{meter_id}" if meter_id else prefix
    config = MeterEnvConfig.from_prefix(env_prefix)
    return config.host, config.port


def list_meter_ids(prefix: str = "METER") -> list[str]:
    """列出配置的电表ID

    Args:
        prefix: 环境变量前缀

    Returns:
        电表ID列表
    """
    pattern = re.compile(rf"^{prefix}_(\d+)_HOST")
    meter_ids = []
    for key in os.environ:
        match = pattern.match(key)
        if match:
            meter_ids.append(match.group(1))
    return sorted(meter_ids, key=int)


# 预设配置
PRESET_PROFILES = {
    "public": {
        "security_level": "public",
        "security_suite": "NONE",
    },
    "low": {
        "security_level": "low",
        "security_suite": "LLS",
    },
    "hls_ism": {
        "security_level": "hls",
        "security_suite": "HLS_ISM",
    },
    "hls_gmac": {
        "security_level": "hls",
        "security_suite": "HLS_GMAC",
    },
    "sm4_gmac": {
        "security_level": "hls",
        "security_suite": "SM4_GMAC",
    },
}


def apply_profile(settings: "DlmsConnectionSettings", profile: str):
    """应用预设配置

    Args:
        settings: 连接设置对象
        profile: 预设名称
    """
    if profile not in PRESET_PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Available: {list(PRESET_PROFILES.keys())}")

    profile_config = PRESET_PROFILES[profile]
    level = profile_config["security_level"]

    if level == "public":
        settings.authentication = "none"
    elif level == "low":
        settings.authentication = "low"
    elif level == "hls":
        settings.authentication = "hls"


# 导出
__all__ = [
    "load_env",
    "get_connection_settings",
    "get_meter_host",
    "list_meter_ids",
    "MeterEnvConfig",
    "apply_profile",
    "PRESET_PROFILES",
]
