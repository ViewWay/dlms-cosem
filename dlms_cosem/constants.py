"""
DLMS/COSEM protocol constants.

This module defines well-known constants used in DLMS/COSEM protocol.
"""

# DLMS/COSEM UDP reserved port (Green Book 7.3.3.4)
# Port 4059 is the IANA-assigned port for DLMS/COSEM over UDP.
DLMS_UDP_PORT: int = 4059

# DLMS/COSEM TCP default port
# While not officially reserved, port 4059 is commonly used for
# DLMS/COSEM over TCP as well.
DLMS_TCP_PORT: int = 4059
