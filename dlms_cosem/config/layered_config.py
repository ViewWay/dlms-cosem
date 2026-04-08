"""DLMS/COSEM Layered Configuration Loader.

按照协议栈层次加载配置:
- Basic:   基础配置
- Key:     密钥配置
- HDLC:    数据链路层配置
- WPDU:    传输层配置 (TCP/IP)
- AARQ:    应用层配置 (认证/加密)

Example usage:
    from dlms_cosem.config.layered_config import LayeredConfig

    # 加载配置
    config = LayeredConfig()

    # 创建连接设置
    settings = config.to_connection_settings()
"""
from __future__ import annotations

import re
import os
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from pathlib import Path


# ============================================================
# 数据类定义
# ============================================================

@dataclass
class BasicConfig:
    """基础配置"""
    get_frame_counter: str = "always"  # always, attribute, never
    public_client_id: int = 16
    frame_counter_mode: str = "attribute"
    frame_counter_obis: str = "0.0.43.1.0.255"


@dataclass
class KeyConfig:
    """密钥配置"""
    # LLS密钥
    lls_key: str = "3030303030303030"

    # HLS密钥
    hls_key: str = "30303030303030303030303030303030"

    # 加密密钥 (EKEY)
    ekey: str = "000102030405060708090A0B0C0D0E0F"

    # 认证密钥 (AKEY)
    akey: str = "D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF"

    # ECDSA密钥
    client_private_key: str = ""
    client_public_key: str = ""
    server_public_key: str = ""


@dataclass
class HdlcConfig:
    """HDLC数据链路层配置"""
    # 串口配置
    com_port: str = "/dev/ttyUSB0"
    baud_rate: int = 2400
    data_bits: int = 8
    stop_bits: int = 1
    parity: str = "none"

    # 逻辑地址
    server_logical_address: int = 1
    server_physical_address: int = 17
    client_logical_address: int = 16
    client_physical_address: int = 16

    # 序列号
    client_ssn: int = 0
    client_rsn: int = 0
    server_ssn: int = 0
    server_rsn: int = 0

    # 数据传输
    max_data_size: int = 128
    window_size: int = 1
    repeat_count: int = 3


@dataclass
class WpduConfig:
    """WPDU传输层配置 (TCP/IP)"""
    server_ip: str = "localhost"
    server_port: int = 4059

    # 端口
    src_wport: int = 17
    dst_wport: int = 1

    # 超时
    response_timeout: int = 1000
    connection_timeout: int = 5000

    # IP版本
    is_ipv4: bool = True
    is_ipv6: bool = False


@dataclass
class AarqConfig:
    """AARQ应用层配置 (认证/加密)"""
    # 认证机制
    # 0: No Security, 1: LLS, 2: HLS_GMAC, 3: HLS_SHA256, 4: HLS_ECDSA
    authentication_mechanism: int = 2

    # 认证密钥
    authentication_key: str = ""
    authentication_key_length: int = 16
    authentication_key_mode: int = 2
    authentication_key_mode_length: int = 16

    # 中国国标
    usage_gbt: bool = False

    # PDU大小
    client_max_receive_pdu_size: int = 65535
    server_max_receive_pdu_size: int = 65535

    # 系统标题
    system_title_client: str = "MDMID000"
    system_title_server: str = ""
    calling_ae_qualifier: str = ""

    # 访问级别
    access_level: int = 2
    mechanism: int = 2
    protection_type: int = 0

    # 签名
    signature: bool = False

    # 应用上下文
    application_context_name: str = "LNC"

    # 加密策略
    security_policy: str = "02"


@dataclass
class MeterConfig:
    """完整电表配置 (分层)"""
    meter_id: str = "default"
    basic: BasicConfig = field(default_factory=BasicConfig)
    key: KeyConfig = field(default_factory=KeyConfig)
    hdlc: HdlcConfig = field(default_factory=HdlcConfig)
    wpdu: WpduConfig = field(default_factory=WpduConfig)
    aarq: AarqConfig = field(default_factory=AarqConfig)


# ============================================================
# 配置解析器
# ============================================================

class LayeredConfigParser:
    """分层配置解析器"""

    # 部分到配置类的映射
    SECTION_CLASSES = {
        "Basic": BasicConfig,
        "Key": KeyConfig,
        "HDLC": HdlcConfig,
        "WPDU": WpduConfig,
        "AARQ": AarqConfig,
    }

    def __init__(self):
        self._raw_config: Dict[str, Any] = {}

    def parse_yaml(self, content: str) -> Dict[str, Dict[str, Any]]:
        """解析YAML格式配置"""
        import yaml
        return yaml.safe_load(content) or {}

    def parse_env(self) -> Dict[str, Dict[str, Any]]:
        """从环境变量解析配置

        支持格式:
        - Basic_getFrameCounter
        - HDLC_serverLogicalAddress
        - METER_001_HDLC_serverLogicalAddress
        """
        config = {
            "Basic": {},
            "Key": {},
            "HDLC": {},
            "WPDU": {},
            "AARQ": {},
        }

        for key, value in os.environ.items():
            # 解析 METER_ID_SECTION_KEY 格式
            match = re.match(r"^METER_(\d+)_(\w+)_(\w+)$", key)
            if match:
                meter_id, section, param = match.groups()
                if meter_id not in config:
                    config[f"METER_{meter_id}"] = {}
                if section not in config[f"METER_{meter_id}"]:
                    config[f"METER_{meter_id}"][section] = {}
                config[f"METER_{meter_id}"][section][param] = value
                continue

            # 解析 SECTION_KEY 格式
            match = re.match(r"^(\w+)_(\w+)$", key)
            if match:
                section, param = match.groups()
                if section in config:
                    config[section][param] = value

        return config

    def parse_file(self, path: str) -> Dict[str, Dict[str, Any]]:
        """解析配置文件 (支持YAML和自定义格式)"""
        path_obj = Path(path)

        if not path_obj.exists():
            return {}

        with open(path_obj, "r", encoding="utf-8") as f:
            content = f.read()

        # 尝试YAML格式
        try:
            return self.parse_yaml(content)
        except Exception:
            pass

        # 解析自定义格式 (key: value 或 key:value)
        return self._parse_custom_format(content)

    def _parse_custom_format(self, content: str) -> Dict[str, Dict[str, Any]]:
        """解析自定义格式配置

        格式:
        Section:
          key: value
        """
        config = {
            "Basic": {},
            "Key": {},
            "HDLC": {},
            "WPDU": {},
            "AARQ": {},
        }

        current_section = None
        current_meter = None

        for line in content.splitlines():
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith("#"):
                continue

            # 检查是否是节标题 (Section:)
            if line.endswith(":"):
                section = line[:-1].strip()

                # 检查是否是电表特定配置
                if section.startswith("METER_"):
                    current_meter = section
                    config[current_meter] = {}
                    current_section = None
                elif section in self.SECTION_CLASSES:
                    current_section = section
                    current_meter = None
                else:
                    # 子节
                    if current_meter:
                        if current_meter not in config:
                            config[current_meter] = {}
                        config[current_meter][section] = {}
                    current_section = section
                continue

            # 解析键值对
            if ":" in line or " :" in line:
                parts = re.split(r"\s*:\s*", line, 1)
                if len(parts) == 2:
                    key, value = parts
                    value = value.strip().strip('"').strip("'")

                    if current_meter:
                        if current_section not in config.get(current_meter, {}):
                            if current_meter not in config:
                                config[current_meter] = {}
                            config[current_meter][current_section] = {}
                        config[current_meter][current_section][key] = value
                    elif current_section:
                        config[current_section][key] = value

        return config

    def create_config(
        self,
        parsed: Dict[str, Dict[str, Any]],
        meter_id: Optional[str] = None,
    ) -> MeterConfig:
        """创建电表配置对象

        Args:
            parsed: 解析后的配置字典
            meter_id: 电表ID (如 "001")

        Returns:
            电表配置对象
        """
        # 合并默认配置和电表特定配置
        meter_key = f"METER_{meter_id}" if meter_id else None
        sections = ["Basic", "Key", "HDLC", "WPDU", "AARQ"]

        configs = {}
        for section in sections:
            section_data = {}

            # 先添加默认配置
            if section in parsed:
                section_data.update(parsed[section])

            # 覆盖电表特定配置
            if meter_key and meter_key in parsed:
                if section in parsed[meter_key]:
                    section_data.update(parsed[meter_key][section])

            configs[section] = section_data

        return MeterConfig(
            meter_id=meter_id or "default",
            basic=self._create_section(BasicConfig, configs.get("Basic", {})),
            key=self._create_section(KeyConfig, configs.get("Key", {})),
            hdlc=self._create_section(HdlcConfig, configs.get("HDLC", {})),
            wpdu=self._create_section(WpduConfig, configs.get("WPDU", {})),
            aarq=self._create_section(AarqConfig, configs.get("AARQ", {})),
        )

    def _create_section(self, cls, data: Dict[str, Any]):
        """创建配置节对象"""
        # 转换键名 (camelCase -> snake_case)
        converted = {}
        for key, value in data.items():
            snake_key = self._camel_to_snake(key)
            converted[snake_key] = self._convert_value(value, cls, snake_key)

        try:
            return cls(**converted)
        except Exception as e:
            # 如果转换失败，返回默认对象
            return cls()

    def _camel_to_snake(self, name: str) -> str:
        """将camelCase转换为snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _convert_value(self, value: Any, cls, key: str) -> Any:
        """转换值类型"""
        if value is None or value == "":
            # 获取默认值
            if hasattr(cls, "__dataclass_fields__"):
                fields = cls.__dataclass_fields__
                if key in fields:
                    return fields[key].default
            return None

        # 尝试转换为bool
        if isinstance(value, str):
            if value.lower() in ("true", "yes", "1"):
                return True
            if value.lower() in ("false", "no", "0"):
                return False

        # 尝试转换为int
        try:
            return int(value)
        except (ValueError, TypeError):
            pass

        return value


# ============================================================
# 主配置类
# ============================================================

class LayeredConfig:
    """分层配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化分层配置

        Args:
            config_path: 配置文件路径
        """
        self._parser = LayeredConfigParser()
        self._config_path = config_path
        self._parsed: Dict[str, Any] = {}
        self._meters: List[str] = []

        # 加载配置
        self._load()

    def _load(self):
        """加载配置文件"""
        if self._config_path:
            self._parsed = self._parser.parse_file(self._config_path)
        else:
            # 从环境变量加载
            self._parsed = self._parser.parse_env()

        # 查找电表ID
        for key in self._parsed:
            if key.startswith("METER_"):
                meter_id = key.replace("METER_", "")
                if meter_id not in self._meters:
                    self._meters.append(meter_id)

    def get_meter(self, meter_id: Optional[str] = None) -> MeterConfig:
        """获取电表配置

        Args:
            meter_id: 电表ID (如 "001")，None表示默认配置

        Returns:
            电表配置对象
        """
        return self._parser.create_config(self._parsed, meter_id)

    def list_meters(self) -> List[str]:
        """列出所有配置的电表ID"""
        return self._meters

    def to_connection_settings(self, meter_id: Optional[str] = None):
        """转换为DLMS连接设置

        Args:
            meter_id: 电表ID

        Returns:
            DlmsConnectionSettings对象
        """
        from dlms_cosem import DlmsConnectionSettings

        config = self.get_meter(meter_id)

        settings = DlmsConnectionSettings(
            client_logical_address=config.hdlc.client_logical_address,
            server_logical_address=config.hdlc.server_logical_address,
        )

        # 根据认证机制设置
        auth_mech = config.aarq.authentication_mechanism

        if auth_mech == 0:
            settings.authentication = "none"
        elif auth_mech == 1:
            settings.authentication = "low"
            settings.password = config.key.lls_key[:8].encode("ascii")
        elif auth_mech in (2, 3, 4):
            settings.authentication = "hls"
            if config.key.akey:
                settings.authentication_key = bytes.fromhex(config.key.akey)
            if config.key.ekey:
                settings.encryption_key = bytes.fromhex(config.key.ekey)

        return settings

    def get_host_port(self, meter_id: Optional[str] = None) -> tuple[str, int]:
        """获取主机和端口

        Args:
            meter_id: 电表ID

        Returns:
            (host, port) 元组
        """
        config = self.get_meter(meter_id)
        return config.wpdu.server_ip, config.wpdu.server_port


# ============================================================
# 便捷函数
# ============================================================

def load_layered_config(config_path: Optional[str] = None) -> LayeredConfig:
    """加载分层配置

    Args:
        config_path: 配置文件路径，默认搜索:
                    - ./.env
                    - ./config/meter_config.yaml
                    - ~/.dlms_cosem/config.yaml

    Returns:
        分层配置管理器
    """
    if config_path is None:
        search_paths = [
            Path.cwd() / ".env",
            Path.cwd() / "config" / "meter_config.yaml",
            Path.home() / ".dlms_cosem" / "config.yaml",
        ]
        for path in search_paths:
            if path.exists():
                config_path = str(path)
                break

    return LayeredConfig(config_path)


__all__ = [
    "BasicConfig",
    "KeyConfig",
    "HdlcConfig",
    "WpduConfig",
    "AarqConfig",
    "MeterConfig",
    "LayeredConfig",
    "LayeredConfigParser",
    "load_layered_config",
]
