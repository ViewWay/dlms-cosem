"""Singleton pattern implementation for DLMS/COSEM.

This module provides a thread-safe singleton class for global state management.
Use for compatibility with legacy code patterns.

Reference: pdlms/pdlms/util/singleton.py
"""

import threading


class Singleton:
    """
    Thread-safe singleton for managing global state.

    Provides class-level attributes for storing connection objects,
    configuration parameters, and communication state.

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
        ObisDataType: OBIS data type mapping
        MetersLogsDict: Meter logs dictionary
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
    ObisDataType: dict[str, type] = {}
    MetersLogsDict: dict[str, list] = {}
    SendFrameControl = ""
    RecvFrameControl = ""
    _instance_lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Create or return singleton instance with thread safety.

        Returns:
            Singleton instance
        """
        if cls._instance is None:
            with cls._instance_lock:
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
