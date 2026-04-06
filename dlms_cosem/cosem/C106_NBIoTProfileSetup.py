"""IC class 106 - NB-IoT Profile Setup.

Configuration for NB-IoT (Narrowband IoT) communication.
Blue Book addition for LPWAN smart metering.

Supports:
- APN/PLMN configuration
- PSM/eDRX power saving modes
- NIDD (Non-IP Data Delivery)
- CoAP/UDP transport
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class NBIoTProfileSetup:
    """COSEM IC NB-IoT Profile Setup (class_id=106).

    Attributes:
        1: logical_name (static)
        2: plmn (static) - PLMN ID (MCC+MNC)
        3: apn (static) - Access Point Name
        4: band (static) - operating band
        5: psm_enabled (static) - Power Saving Mode
        6: psm_tau (static) - TAU timer (seconds)
        7: psm_active (static) - Active timer (seconds)
        8: edrx_enabled (static) - eDRX mode
        9: edrx_value (static) - eDRX cycle value
        10: edrx_ptw (static) - Paging Time Window
        11: nidd_enabled (static) - Non-IP Data Delivery
        12: coap_port (static) - CoAP port number
        13: dtls_enabled (static) - DTLS security
        14: status (dynamic)
    Methods:
        1: connect
        2: disconnect
        3: reset
    """

    CLASS_ID: ClassVar[int] = 106
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    plmn: Optional[str] = None  # e.g. "46000" for China Mobile
    apn: Optional[str] = None
    band: int = 8  # B8 (900MHz) common for China
    psm_enabled: bool = True
    psm_tau: int = 43200  # 12 hours default
    psm_active: int = 10  # 10 seconds
    edrx_enabled: bool = False
    edrx_value: float = 81.92  # seconds
    edrx_ptw: float = 2.56  # seconds
    nidd_enabled: bool = False
    coap_port: int = 5683
    dtls_enabled: bool = True
    status: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="plmn"),
        3: AttributeDescription(attribute_id=3, attribute_name="apn"),
        4: AttributeDescription(attribute_id=4, attribute_name="band"),
        5: AttributeDescription(attribute_id=5, attribute_name="psm_enabled"),
        6: AttributeDescription(attribute_id=6, attribute_name="psm_tau"),
        7: AttributeDescription(attribute_id=7, attribute_name="psm_active"),
        8: AttributeDescription(attribute_id=8, attribute_name="edrx_enabled"),
        9: AttributeDescription(attribute_id=9, attribute_name="edrx_value"),
        10: AttributeDescription(attribute_id=10, attribute_name="edrx_ptw"),
        11: AttributeDescription(attribute_id=11, attribute_name="nidd_enabled"),
        12: AttributeDescription(attribute_id=12, attribute_name="coap_port"),
        13: AttributeDescription(attribute_id=13, attribute_name="dtls_enabled"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        14: AttributeDescription(attribute_id=14, attribute_name="status"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "connect", 2: "disconnect", 3: "reset"}

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def reset(self) -> None:
        self.status = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
