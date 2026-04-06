"""IC class 66 - MeasurementDataMonitoring.

Measurement Data Monitoring - monitors measurement data with trigger-based capture.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=66
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class MeasurementDataMonitoring:
    """COSEM IC MeasurementDataMonitoring (class_id=66).

    Attributes:
        1: logical_name (static)
        2: status (dynamic)
        3: trigger_source (dynamic)
        4: sampling_rate (dynamic)
        5: number_of_samples_before_trigger (dynamic)
        6: number_of_samples_after_trigger (dynamic)
        7: trigger_time (dynamic)
        8: scaler_unit (dynamic)
    Methods:
        1: reset
        2: capture
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MEASUREMENT_DATA_MONITORING
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    status: Optional[int] = 0
    trigger_source: Optional[int] = 0
    sampling_rate: Optional[int] = 0
    number_of_samples_before_trigger: Optional[int] = 0
    number_of_samples_after_trigger: Optional[int] = 0
    trigger_time: Optional[bytes] = None
    scaler_unit: Optional[Any] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'status', 3: 'trigger_source', 4: 'sampling_rate', 5: 'number_of_samples_before_trigger', 6: 'number_of_samples_after_trigger', 7: 'trigger_time', 8: 'scaler_unit'}
    METHODS: ClassVar[Dict[int, str]] = {1: 'reset', 2: 'capture'}

    def reset(self) -> None:
        """Method 1: reset."""

    def capture(self) -> None:
        """Method 2: capture."""

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

