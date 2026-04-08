"""Singleton pattern implementation for DLMS/COSEM.

This module provides a thread-safe singleton class for global state management.
Use for compatibility with legacy code patterns.

Reference: pdlms/pdlms/util/singleton.py

WARNING: The ObisDataType and MetersLogsDict dictionaries can accumulate
unbounded data. Call reset() or clear_cache() periodically to prevent memory leaks.
"""

import threading
from typing import Dict, Any


class Singleton:
    """
    Thread-safe singleton for managing global state.

    Provides class-level attributes for storing connection objects,
    configuration parameters, and communication state.

    WARNING: ObisDataType and MetersLogsDict can grow unbounded.
    Use clear_cache() to reset them when needed.

    Attributes:
        CONN: Connection object
        CMCS: CMCS (Key Management System) object
        Project: Project metadata
        Communication: Communication type string
        ConnectType: Connection type
        ComPort: Serial port name
        ClientId: Client ID for GPRS
        ServerIpAddress: Server IP address
        ServerIpPort: Server IP port
        IsIPv4Udp: IPv4 UDP flag
        IsIPv6Udp: IPv6 UDP flag
        MeterNo: Meter number (serial)
        HdlcHeartBeatTimeOut: HDLC heartbeat timeout (seconds)
        WpduHeartBeatTimeOut: WPDU heartbeat timeout (seconds)
        DefaultConfigAddress: Default configuration address
        ObisDataType: OBIS data type mapping (WARNING: can grow unbounded)
        MetersLogsDict: Meter logs dictionary (WARNING: can grow unbounded)
        SendFrameControl: Send frame control string
        RecvFrameControl: Receive frame control string
    """

    CONN = None
    CMCS = None
    Project = None
    Communication = ""
    ConnectType = None
    ComPort = ""
    ClientId = ""
    ServerIpAddress = ""
    ServerIpPort = ""
    IsIPv4Udp = 0
    IsIPv6Udp = 0
    MeterNo = ""
    HdlcHeartBeatTimeOut = 120
    WpduHeartBeatTimeOut = 60
    DefaultConfigAddress = "192.168.234.194"
    ObisDataType: Dict[str, Any] = {}
    MetersLogsDict: Dict[str, Any] = {}
    SendFrameControl = ""
    RecvFrameControl = ""
    _instance_lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Create or return singleton instance with thread safety.

        Uses double-check locking pattern for thread safety.

        Returns:
            Singleton instance
        """
        # Fast path: check class variable without lock
        if cls._instance is not None:
            return cls._instance

        # Slow path: acquire lock and check again
        with cls._instance_lock:
            # Double-check: another thread may have created instance
            if cls._instance is None:
                cls._instance = object.__new__(cls)
            return cls._instance

    @classmethod
    def reset(cls):
        """Reset all singleton attributes to default values."""
        cls.CONN = None
        cls.CMCS = None
        cls.Project = None
        cls.Communication = ""
        cls.ConnectType = None
        cls.ComPort = ""
        cls.ClientId = ""
        cls.ServerIpAddress = ""
        cls.ServerIpPort = ""
        cls.IsIPv4Udp = 0
        cls.IsIPv6Udp = 0
        cls.MeterNo = ""
        cls.HdlcHeartBeatTimeOut = 120
        cls.WpduHeartBeatTimeOut = 60
        cls.DefaultConfigAddress = "192.168.234.194"
        cls.ObisDataType = {}
        cls.MetersLogsDict = {}
        cls.SendFrameControl = ""
        cls.RecvFrameControl = ""

    @classmethod
    def clear_cache(cls):
        """Clear cache dictionaries to prevent memory leaks.

        Call this periodically if your application uses ObisDataType
        or MetersLogsDict extensively.
        """
        cls.ObisDataType.clear()
        cls.MetersLogsDict.clear()

    @classmethod
    def get_cache_size(cls) -> dict:
        """Get approximate size of cached dictionaries.

        Returns:
            Dict with 'obis_data_count' and 'meters_logs_count' keys
        """
        return {
            "obis_data_count": len(cls.ObisDataType),
            "meters_logs_count": len(cls.MetersLogsDict),
        }
