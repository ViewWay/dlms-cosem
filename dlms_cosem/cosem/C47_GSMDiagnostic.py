"""IC class 47 - GSMDiagnostic.

GSM Diagnostic - provides GSM network diagnostic information.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=47
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class GSMDiagnostic:
    """COSEM IC GSMDiagnostic (class_id=47).

    Attributes:
        1: logical_name (static)
        2: operator (dynamic)
        3: status (dynamic)
        4: circuit_switch_status (dynamic)
        5: packet_switch_status (dynamic)
        6: cell_id (dynamic)
        7: location_area (dynamic)
        8: vci (dynamic)
        9: mcc (dynamic)
        10: mnc (dynamic)
        11: base_station_id (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.GSM_DIAGNOSTICS
    VERSION: ClassVar[int] = 2

    logical_name: Obis
    operator: Optional[str] = ''
    status: Optional[int] = 0
    circuit_switch_status: Optional[int] = 0
    packet_switch_status: Optional[int] = 0
    cell_id: Optional[int] = 0
    location_area: Optional[int] = 0
    vci: Optional[int] = 0
    mcc: Optional[int] = 0
    mnc: Optional[int] = 0
    base_station_id: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'operator', 3: 'status', 4: 'circuit_switch_status', 5: 'packet_switch_status', 6: 'cell_id', 7: 'location_area', 8: 'vci', 9: 'mcc', 10: 'mnc', 11: 'base_station_id'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

