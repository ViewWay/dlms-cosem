from datetime import datetime, timedelta
from typing import *

import attr

from dlms_cosem import a_xdr, cosem, enumerations
from dlms_cosem.cosem import CosemAttribute
from dlms_cosem.cosem.C15_AssociationLN import (
    AccessRight,
    AssociationObjectListItem,
    AttributeAccessRights,
    MethodAccessRights,
)
from dlms_cosem.time import datetime_from_bytes


@attr.s(auto_attribs=True)
class ColumnValue:

    attribute: CosemAttribute
    value: Any


@attr.s(auto_attribs=True)
class ProfileGenericBufferParser:
    """
    Parser for DLMS/COSEM Profile Generic buffer data.

    Profile Generic objects (interface class 7) store historical data
    such as load profiles, event logs, or meter readings. The buffer contains
    multiple columns (capture objects) and multiple entries (rows).

    This parser handles:
        - Decoding A-XDR encoded profile data
        - Clock timestamp expansion (null value compression)
        - Column filtering (parse only specific columns)
        - Entry range filtering (parse only specific rows)

    Attributes:
        capture_objects: List of COSEM attributes representing each column
        capture_period: Time between entries in minutes (for timestamp expansion)
        from_column: Starting column index for filtering (1-based, optional)
        to_column: Ending column index for filtering (0 means last column, optional)

    Examples:
        Basic parsing:
        >>> parser = ProfileGenericBufferParser(
        ...     capture_objects=[clock_attr, register_attr],
        ...     capture_period=15
        ... )
        >>> parsed = parser.parse_bytes(raw_data)

        With column filtering:
        >>> parser = ProfileGenericBufferParser.with_column_filter(
        ...     capture_objects=[clock_attr, register1, register2],
        ...     capture_period=15,
        ...     from_column=1,
        ...     to_column=2  # Only parse first 2 columns
        ... )

        Parse specific entry range:
        >>> parser = ProfileGenericBufferParser(...)
        >>> parsed = parser.parse_entries_with_range(
        ...     entries=raw_entries,
        ...     from_entry=1,
        ...     to_entry=100
        ... )
    """

    capture_objects: List[CosemAttribute]
    capture_period: int  # minutes
    from_column: Optional[int] = attr.ib(default=None)
    to_column: Optional[int] = attr.ib(default=None)

    def _get_filtered_columns(self) -> List[CosemAttribute]:
        """
        Get capture objects filtered by column range.

        Column indices are 1-based to match DLMS/COSEM convention.
        from_column=1 means start from first column, to_column=0 means to the last.
        """
        if self.from_column is None and self.to_column is None:
            return self.capture_objects

        from_idx = (self.from_column - 1) if self.from_column else 0
        to_idx = self.to_column if self.to_column else len(self.capture_objects)

        return self.capture_objects[from_idx:to_idx]

    def _filter_entry_columns(self, entry: List[Any]) -> List[Any]:
        """
        Filter an entry's columns based on the configured column range.
        """
        if self.from_column is None and self.to_column is None:
            return entry

        from_idx = (self.from_column - 1) if self.from_column else 0
        to_idx = self.to_column if self.to_column else len(entry)

        return entry[from_idx:to_idx]

    def parse_bytes(self, profile_bytes: bytes):
        """
        Profile generic are sent as a sequence of A-XDR encoded DlmsData.
        """
        data_decoder = a_xdr.AXdrDecoder(
            encoding_conf=a_xdr.EncodingConf(
                attributes=[a_xdr.Sequence(attribute_name="data")]  # type: ignore[abstract,call-arg]
            )
        )
        entries: List[List[Any]] = data_decoder.decode(profile_bytes)["data"]

        return self.parse_entries(entries)

    def parse_entries(
        self, entries: List[List[Optional[Any]]]
    ) -> List[List[Optional[ColumnValue]]]:
        """
        Returns a list of columns with the cosem attribut linked to the value with a
        ColumnValue.
        It also sets the timestamp on each column calculated from the prevoius entry
        if the data has been sent compressed using null values.

        If from_column/to_column are set, only the specified columns will be parsed.
        """
        parsed_entries = list()
        last_entry_timestamp: Optional[datetime] = None

        # Get filtered capture objects based on column range
        filtered_capture_objects = self._get_filtered_columns()

        for entry in entries:
            # Filter entry columns if column range is set
            filtered_entry = self._filter_entry_columns(entry)

            if len(filtered_entry) != len(filtered_capture_objects):
                raise ValueError(
                    f"Unable to parse ProfileGeneric entry as the amount of columns "
                    f"({len(filtered_entry)}) differ from the parsers set capture_object length "
                    f"({len(filtered_capture_objects)}) "
                )
            parsed_column = list()
            for index, column in enumerate(filtered_entry):
                cosem_attribute = filtered_capture_objects[index]
                if column is not None:
                    if cosem_attribute.interface == enumerations.CosemInterface.CLOCK:
                        # parse as time.
                        value = datetime_from_bytes(column)[
                            0
                        ]  # Clock status not used here; only the datetime value is needed.
                        last_entry_timestamp = value
                        parsed_column.append(
                            ColumnValue(attribute=cosem_attribute, value=value)
                        )
                    else:
                        parsed_column.append(
                            ColumnValue(attribute=cosem_attribute, value=column)
                        )
                else:
                    if cosem_attribute.interface == enumerations.CosemInterface.CLOCK:
                        if last_entry_timestamp:
                            value = last_entry_timestamp + timedelta(
                                minutes=self.capture_period
                            )
                            last_entry_timestamp = value
                            parsed_column.append(
                                ColumnValue(attribute=cosem_attribute, value=value)
                            )

                        else:
                            parsed_column.append(None)  # type: ignore[arg-type]

            parsed_entries.append(parsed_column)

        return parsed_entries

    def parse_entries_with_range(
        self,
        entries: List[List[Optional[Any]]],
        from_entry: int = 1,
        to_entry: int = 0,
    ) -> List[List[Optional[ColumnValue]]]:
        """
        Parse entries within a specific entry range.

        Args:
            entries: Raw entry data from profile
            from_entry: Starting entry index (1-based)
            to_entry: Ending entry index (0 means to the last entry)

        Returns:
            Parsed entries within the specified range
        """
        if to_entry == 0:
            to_entry = len(entries)

        # Convert to 0-based indexing
        from_idx = from_entry - 1
        to_idx = min(to_entry, len(entries))

        selected_entries = entries[from_idx:to_idx]
        return self.parse_entries(selected_entries)

    @classmethod
    def with_column_filter(
        cls,
        capture_objects: List[CosemAttribute],
        capture_period: int,
        from_column: int = 1,
        to_column: int = 0,
    ) -> "ProfileGenericBufferParser":
        """
        Create a parser that only parses specific columns.

        Args:
            capture_objects: List of capture objects (columns)
            capture_period: Capture period in minutes
            from_column: Starting column index (1-based, default 1)
            to_column: Ending column index (0 means to the last column, default 0)

        Returns:
            A ProfileGenericBufferParser configured for column filtering

        Example:
            >>> parser = ProfileGenericBufferParser.with_column_filter(
            ...     capture_objects=my_objects,
            ...     capture_period=15,
            ...     from_column=1,
            ...     to_column=5  # Only parse first 5 columns
            ... )
        """
        return cls(
            capture_objects=capture_objects,
            capture_period=capture_period,
            from_column=from_column,
            to_column=to_column if to_column > 0 else None,
        )


class AssociationObjectListParser:
    @staticmethod
    def parse_bytes(profile_bytes: bytes):
        """
        Profile generic are sent as a sequence of A-XDR encoded DlmsData.
        """
        data_decoder = a_xdr.AXdrDecoder(
            encoding_conf=a_xdr.EncodingConf(
                attributes=[a_xdr.Sequence(attribute_name="data")]  # type: ignore[abstract,call-arg]
            )
        )
        entries: List[List[Any]] = data_decoder.decode(profile_bytes)["data"]

        return AssociationObjectListParser.parse_entries(entries)

    @staticmethod
    def parse_access_right(access_right: int) -> List[AccessRight]:
        parsed_access_rights = list()
        if bool(access_right & 0b00000001):
            parsed_access_rights.append(AccessRight.READ_ACCESS.value)
        if bool(access_right & 0b00000010):
            parsed_access_rights.append(AccessRight.WRITE_ACCESS.value)
        if bool(access_right & 0b00000100):
            parsed_access_rights.append(AccessRight.AUTHENTICATED_REQUEST.value)
        if bool(access_right & 0b00001000):
            parsed_access_rights.append(AccessRight.ENCRYPTED_REQUEST.value)
        if bool(access_right & 0b00010000):
            parsed_access_rights.append(AccessRight.DIGITALLY_SIGNED_REQUEST.value)
        if bool(access_right & 0b00100000):
            parsed_access_rights.append(AccessRight.AUTHENTICATED_RESPONSE.value)
        if bool(access_right & 0b01000000):
            parsed_access_rights.append(AccessRight.ENCRYPTED_RESPONSE.value)
        if bool(access_right & 0b10000000):
            parsed_access_rights.append(AccessRight.DIGITALLY_SIGNED_RESPONSE.value)

        return parsed_access_rights

    @staticmethod
    def parse_attribute_access_rights(
        access_rights: List[List[Optional[Union[int, List[int]]]]]
    ):
        parsed_access_rights = list()
        for right in access_rights:
            parsed_access_rights.append(
                AttributeAccessRights(
                    attribute=right[0],
                    access_rights=AssociationObjectListParser.parse_access_right(
                        right[1]
                    ),
                    access_selectors=right[2],
                )
            )
        return parsed_access_rights

    @staticmethod
    def parse_method_access_rights(
        access_rights: List[List[int]],
    ) -> List[MethodAccessRights]:
        parsed_access_rights = list()
        for right in access_rights:
            parsed_access_rights.append(
                MethodAccessRights(
                    method=right[0],
                    access_rights=AssociationObjectListParser.parse_access_right(
                        right[1]
                    ),
                )
            )

        return parsed_access_rights

    @staticmethod
    def parse_entries(object_list):
        parsed_objects = list()
        for obj in object_list:
            interface = enumerations.CosemInterface(obj[0]).value
            version = obj[1]
            logical_name = cosem.Obis.from_bytes(obj[2])
            access_rights = obj[3]
            attribute_access_rights = (
                AssociationObjectListParser.parse_attribute_access_rights(
                    access_rights[0]
                )
            )
            attribute_access_dict = {
                access.attribute: access for access in attribute_access_rights
            }
            method_access_rights = (
                AssociationObjectListParser.parse_method_access_rights(access_rights[1])
            )
            method_access_dict = {
                access.method: access for access in method_access_rights
            }

            parsed_objects.append(
                AssociationObjectListItem(
                    interface=interface,
                    version=version,
                    logical_name=logical_name,
                    attribute_access_rights=attribute_access_dict,
                    method_access_rights=method_access_dict,
                )
            )
        return parsed_objects
