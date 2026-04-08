"""
wPort constants for DLMS/COSEM (Green Book 7.3.3.4).

Wrapper port numbers (wPort) are used for addressing DLMS/COSEM
Application Entities in UDP and TCP transport layers.
"""

# Reserved wrapper port numbers
WPORT_DLMS_COSEM_UDP = 4059  # DLMS/COSEM UDP
WPORT_DLMS_COSEM_TCP = 4059  # DLMS/COSEM TCP

# Client side reserved addresses
WPORT_NO_STATION = 0x0000  # No-station
WPORT_CLIENT_MANAGEMENT_PROCESS = 0x0001  # Client Management Process
WPORT_PUBLIC_CLIENT = 0x0010  # Public Client

# Server side reserved addresses
WPORT_MANAGEMENT_LOGICAL_DEVICE = 0x0001  # Management Logical Device
WPORT_ALL_STATION = 0x007F  # All-station (Broadcast)


def is_reserved_wport(wport: int) -> bool:
    """
    Check if a wPort number is reserved.
    
    Args:
        wport: Wrapper port number to check
        
    Returns:
        True if the wPort is reserved, False otherwise
    """
    reserved_ports = [
        WPORT_NO_STATION,
        WPORT_CLIENT_MANAGEMENT_PROCESS,
        WPORT_PUBLIC_CLIENT,
        WPORT_MANAGEMENT_LOGICAL_DEVICE,
        WPORT_ALL_STATION,
    ]
    
    return wport in reserved_ports


def get_wport_description(wport: int) -> str:
    """
    Get a description of a wPort number.
    
    Args:
        wport: Wrapper port number
        
    Returns:
        Description string
    """
    descriptions = {
        WPORT_NO_STATION: "No-station",
        WPORT_CLIENT_MANAGEMENT_PROCESS: "Client Management Process",
        WPORT_PUBLIC_CLIENT: "Public Client",
        WPORT_MANAGEMENT_LOGICAL_DEVICE: "Management Logical Device",
        WPORT_ALL_STATION: "All-station (Broadcast)",
        WPORT_DLMS_COSEM_UDP: "DLMS/COSEM UDP",
        WPORT_DLMS_COSEM_TCP: "DLMS/COSEM TCP",
    }
    
    return descriptions.get(wport, f"Unknown (0x{wport:04X})")
