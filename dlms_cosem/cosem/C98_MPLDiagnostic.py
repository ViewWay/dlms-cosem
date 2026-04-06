"""IC class 98 - MPLDiagnostic.

MPL Diagnostic - MPL (Multicast Protocol for Low-Power and Lossy Networks) diagnostics.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=98
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class MPLDiagnostic:
    """COSEM IC MPLDiagnostic (class_id=98).

    Attributes:
        1: logical_name (static)
        2: mpl_domain_id (dynamic)
        3: mpl_seed_set_version (dynamic)
        4: mpl_trickle_timer_expirations (dynamic)
        5: mpl_messages_sent (dynamic)
        6: mpl_messages_received (dynamic)
        7: mpl_messages_forwarded (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MPL_DIAGNOSTICS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mpl_domain_id: Optional[bytes] = None
    mpl_seed_set_version: Optional[int] = 0
    mpl_trickle_timer_expirations: Optional[int] = 0
    mpl_messages_sent: Optional[int] = 0
    mpl_messages_received: Optional[int] = 0
    mpl_messages_forwarded: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'mpl_domain_id', 3: 'mpl_seed_set_version', 4: 'mpl_trickle_timer_expirations', 5: 'mpl_messages_sent', 6: 'mpl_messages_received', 7: 'mpl_messages_forwarded'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

