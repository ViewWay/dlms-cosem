"""Bridge between SML and DLMS/COSEM data models."""
from __future__ import annotations

from typing import List, dict

from dlms_cosem.sml.models import SMLValueEntry
from dlms_cosem.sml.parser import SMLParser


class SMLToDLMSBridge:
    """Bridge between SML and DLMS/COSEM data models.

    Converts SML value entries to COSEM OBIS format for interoperability.
    """

    # Common SML OBIS codes mapped to COSEM names
    OBIS_MAP = {
        "1.0.1.8.0.255": "Active Power +",
        "1.0.2.8.0.255": "Active Power -",
        "1.0.31.7.0.255": "Voltage L1",
        "1.0.51.7.0.255": "Current L1",
        "1.0.1.7.0.255": "Active Power Total +",
        "0.0.96.1.0.255": "Server ID",
        "0.0.0.9.0.255": "Meter Firmware Version",
        "1.0.0.0.0.255": "Meter Address",
    }

    @classmethod
    def sml_entry_to_cosem(cls, entry: SMLValueEntry) -> dict:
        """Convert SML entry to COSEM-compatible dict."""
        return {
            "obis": entry.obis_str,
            "value": entry.value,
            "unit": entry.unit,
            "scaler": entry.scaler,
            "cosem_name": cls.OBIS_MAP.get(entry.obis_str, "Unknown"),
        }

    @classmethod
    def obis_bytes_to_str(cls, obis: bytes) -> str:
        """Convert OBIS bytes to string."""
        if len(obis) >= 6:
            return f"{obis[0]}.{obis[1]}.{obis[2]}.{obis[3]}.{obis[4]}.{obis[5]}"
        return ".".join(str(b) for b in obis)

    @classmethod
    def parse_meter_data(cls, data: bytes) -> List[dict]:
        """Parse SML data and return COSEM-compatible entries."""
        parser = SMLParser()
        sml_file = parser.parse(data)
        entries = sml_file.get_value_entries()
        return [cls.sml_entry_to_cosem(e) for e in entries]
