"""IC class 151 - LTEMonitoring.

LTE Monitoring - provides LTE network monitoring information.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=151
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class LTEMonitoring:
    """COSEM IC LTEMonitoring (class_id=151).

    Attributes:
        1: logical_name (static)
        2: operator (dynamic)
        3: signal_strength (dynamic)
        4: noise_level (dynamic)
        5: status (dynamic)
        6: circuit_switch_status (dynamic)
        7: packet_switch_status (dynamic)
        8: cell_id (dynamic)
        9: location_area (dynamic)
        10: vci (dynamic)
        11: mcc (dynamic)
        12: mnc (dynamic)
        13: base_station_id (dynamic)
        14: sim_status (dynamic)
        15: roaming_status (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LTE_MONITORING
    VERSION: ClassVar[int] = 1

    logical_name: Obis
    operator: Optional[str] = ''
    signal_strength: Optional[int] = 0
    noise_level: Optional[int] = 0
    status: Optional[int] = 0
    circuit_switch_status: Optional[int] = 0
    packet_switch_status: Optional[int] = 0
    cell_id: Optional[int] = 0
    location_area: Optional[int] = 0
    vci: Optional[int] = 0
    mcc: Optional[int] = 0
    mnc: Optional[int] = 0
    base_station_id: Optional[int] = 0
    sim_status: Optional[int] = 0
    roaming_status: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'operator', 3: 'signal_strength', 4: 'noise_level', 5: 'status', 6: 'circuit_switch_status', 7: 'packet_switch_status', 8: 'cell_id', 9: 'location_area', 10: 'vci', 11: 'mcc', 12: 'mnc', 13: 'base_station_id', 14: 'sim_status', 15: 'roaming_status'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

