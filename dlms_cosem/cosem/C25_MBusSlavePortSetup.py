"""IC class 25 - MBusSlavePortSetup.

M-Bus Slave Port Setup - configuration for M-Bus slave port.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=25
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class MBusSlavePortSetup:
    """COSEM IC MBusSlavePortSetup (class_id=25).

    Attributes:
        1: logical_name (static)
        2: primary_address (dynamic)
        3: identification_number (dynamic)
        4: manufacturer_id (dynamic)
        5: version (dynamic)
        6: device_type (dynamic)
        7: access_number (dynamic)
        8: status (dynamic)
        9: aligned (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MBUS_SLAVE_PORT_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    primary_address: Optional[int] = 0
    identification_number: Optional[int] = 0
    manufacturer_id: Optional[int] = 0
    version: Optional[int] = 0
    device_type: Optional[int] = 0
    access_number: Optional[int] = 0
    status: Optional[int] = 0
    aligned: Optional[bool] = False

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'primary_address', 3: 'identification_number', 4: 'manufacturer_id', 5: 'version', 6: 'device_type', 7: 'access_number', 8: 'status', 9: 'aligned'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

