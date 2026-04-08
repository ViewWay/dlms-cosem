#!/usr/bin/env python3
"""
Profile Generic Read Methods Example

This example demonstrates how to read Profile Generic (load profile) data
using different access methods:

1. ReadByRange: Read data within a specific time range
2. ReadByEntry: Read data by entry index with optional column filtering

Profile Generic objects are commonly used in smart meters to store
historical data such as energy consumption values over time.
"""
from datetime import datetime, timedelta

from dlms_cosem import cosem, enumerations
from dlms_cosem.cosem.capture_object import CaptureObject
from dlms_cosem.cosem.selective_access import EntryDescriptor, RangeDescriptor
from dlms_cosem.parsers import ColumnValue, ProfileGenericBufferParser


def example_read_by_range():
    """
    Example 1: Reading profile data within a time range.

    ReadByRange uses a RangeDescriptor to filter data by timestamp.
    Only entries with timestamps in the specified range are returned.
    """
    print("=== Example 1: ReadByRange (Time-based filtering) ===\n")

    # Define the Profile Generic object (buffer attribute)
    profile_attribute = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.PROFILE_GENERIC,
        instance=cosem.Obis.from_string("1.0.99.1.0.255"),  # Load profile OBIS
        attribute=2,  # Buffer attribute
    )

    # Define time range
    from_value = datetime(2024, 1, 1, 0, 0, 0)
    to_value = datetime(2024, 1, 31, 23, 59, 59)

    print(f"Reading profile data for: {profile_attribute.instance}")
    print(f"From: {from_value}")
    print(f"To: {to_value}")
    print()

    # Create RangeDescriptor
    # The restricting_object specifies which column contains the timestamp
    restricting_object = CaptureObject(
        cosem_attribute=cosem.CosemAttribute(
            interface=enumerations.CosemInterface.PROFILE_GENERIC,
            instance=cosem.Obis.from_string("1.0.99.1.0.255"),
            attribute=3,  # capture_objects attribute
        ),
        data_index=0,  # First column (typically timestamp)
    )

    range_descriptor = RangeDescriptor(
        restricting_object=restricting_object,
        from_value=from_value,
        to_value=to_value,
    )

    # Simulate using get_with_range (if using DlmsClient)
    print("Usage with DlmsClient:")
    print("  data = client.get_with_range(")
    print(f"      cosem_attribute=profile_attribute,")
    print(f"      from_value=datetime(2024, 1, 1),")
    print(f"      to_value=datetime(2024, 1, 31)")
    print("  )")
    print()


def example_read_by_entry_basic():
    """
    Example 2: Reading profile data by entry index.

    ReadByEntry uses an EntryDescriptor to read specific entries
    without needing to know the timestamps.
    """
    print("=== Example 2: ReadByEntry (Index-based filtering) ===\n")

    profile_attribute = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.PROFILE_GENERIC,
        instance=cosem.Obis.from_string("1.0.99.1.0.255"),
        attribute=2,
    )

    # Read first 100 entries (all columns)
    print("Reading first 100 entries (all columns):")
    print("  data = client.get_with_entry(")
    print(f"      cosem_attribute=profile_attribute,")
    print("      from_entry=1,")
    print("      to_entry=100")
    print("  )")
    print()


def example_read_by_entry_column_filtering():
    """
    Example 3: Reading specific columns.

    EntryDescriptor supports column filtering to reduce
    the amount of data transferred and parsed.
    """
    print("=== Example 3: Column Filtering ===\n")

    profile_attribute = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.PROFILE_GENERIC,
        instance=cosem.Obis.from_string("1.0.99.1.0.255"),
        attribute=2,
    )

    # Read first 100 entries, but only columns 1-5
    # This is useful when you only need specific values
    print("Reading first 100 entries, columns 1-5:")
    print("  data = client.get_with_entry(")
    print(f"      cosem_attribute=profile_attribute,")
    print("      from_entry=1,")
    print("      to_entry=100,")
    print("      from_selected_value=1,")
    print("      to_selected_value=5  # Only columns 1-5")
    print("  )")
    print()

    print("Benefits of column filtering:")
    print("  - Reduced data transfer")
    print("  - Faster parsing")
    print("  - Lower memory usage")
    print("  - Only get the data you need")
    print()


def example_parser_with_column_filter():
    """
    Example 4: Using ProfileGenericBufferParser with column filtering.

    The parser can be configured to only parse specific columns,
    which is useful when working with large profiles.
    """
    print("=== Example 4: Parser with Column Filtering ===\n")

    # Define capture objects (columns in the profile)
    capture_objects = [
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.CLOCK,
            instance=cosem.Obis.from_string("1.0.0.1.0.255"),
            attribute=2,
        ),
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.REGISTER,
            instance=cosem.Obis.from_string("1.0.1.1.0.255"),
            attribute=2,
        ),
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.REGISTER,
            instance=cosem.Obis.from_string("1.0.1.2.0.255"),
            attribute=2,
        ),
    ]

    # Create parser with column filtering (only first 2 columns)
    parser = ProfileGenericBufferParser.with_column_filter(
        capture_objects=capture_objects,
        capture_period=15,  # 15 minutes between entries
        from_column=1,
        to_column=2,  # Only parse first 2 columns
    )

    print(f"Parser configured to parse columns 1-2 only")
    print(f"  Column 1: {capture_objects[0].interface.name} (timestamp)")
    print(f"  Column 2: {capture_objects[1].interface.name}")
    print()


def example_parse_entries_with_range():
    """
    Example 5: Parsing specific entry range.

    The parser can also filter by entry range after
    the data has been retrieved.
    """
    print("=== Example 5: Parse Entry Range ===\n")

    capture_objects = [
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.CLOCK,
            instance=cosem.Obis.from_string("1.0.0.1.0.255"),
            attribute=2,
        ),
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.REGISTER,
            instance=cosem.Obis.from_string("1.0.1.1.0.255"),
            attribute=2,
        ),
    ]

    parser = ProfileGenericBufferParser(
        capture_objects=capture_objects,
        capture_period=15,
    )

    # Simulate parsing entries 10-20 from retrieved data
    print("Usage:")
    print("  # Get raw data from meter")
    print("  data = client.get(profile_attribute)")
    print()
    print("  # Parse entries 10-20 only")
    print("  parsed_data = parser.parse_entries_with_range(")
    print("      entries=raw_entries,")
    print("      from_entry=10,")
    print("      to_entry=20")
    print("  )")
    print()


def example_combined_approach():
    """
    Example 6: Combined approach for efficient data retrieval.

    Shows how to combine ReadByEntry and parser filtering for
    maximum efficiency.
    """
    print("=== Example 6: Combined Efficient Approach ===\n")

    profile_attribute = cosem.CosemAttribute(
        interface=enumerations.CosemInterface.PROFILE_GENERIC,
        instance=cosem.Obis.from_string("1.0.99.1.0.255"),
        attribute=2,
    )

    # Step 1: Use ReadByEntry to get only needed columns
    print("Step 1: Request only needed columns from meter")
    print("  data = client.get_with_entry(")
    print(f"      cosem_attribute=profile_attribute,")
    print("      from_entry=1,")
    print("      to_entry=1000,")
    print("      from_selected_value=1,")
    print("      to_selected_value=3  # Only 3 columns")
    print("  )")
    print()

    # Step 2: Parse with column filter (double filtering)
    capture_objects = [
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.CLOCK,
            instance=cosem.Obis.from_string("1.0.0.1.0.255"),
            attribute=2,
        ),
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.REGISTER,
            instance=cosem.Obis.from_string("1.0.1.1.0.255"),
            attribute=2,
        ),
        cosem.CosemAttribute(
            interface=enumerations.CosemInterface.REGISTER,
            instance=cosem.Obis.from_string("1.0.1.2.0.255"),
            attribute=2,
        ),
    ]

    parser = ProfileGenericBufferParser.with_column_filter(
        capture_objects=capture_objects,
        capture_period=15,
        from_column=1,
        to_column=2,  # Only parse first 2 columns
    )

    print("Step 2: Parse only first 2 columns")
    print("  parsed = parser.parse_bytes(data)")
    print()

    print("Benefits:")
    print("  - Meter only sends 3 columns instead of all")
    print("  - Parser only processes 2 columns")
    print("  - Memory usage minimized")
    print("  - Processing time reduced")
    print()


def example_access_descriptor_factory():
    """
    Example 7: Using AccessDescriptorFactory.

    The factory can parse access descriptors from bytes,
    useful for handling meter responses.
    """
    print("=== Example 7: Access Descriptor Factory ===\n")

    # Create an EntryDescriptor
    entry_desc = EntryDescriptor(
        from_entry=1,
        to_entry=100,
        from_selected_value=1,
        to_selected_value=5,
    )

    # Encode to bytes
    encoded = entry_desc.to_bytes()
    print(f"Encoded EntryDescriptor: {encoded.hex()}")
    print()

    # Decode using factory (for parsing meter responses)
    from dlms_cosem.cosem.selective_access import AccessDescriptorFactory

    decoded = AccessDescriptorFactory.from_bytes(encoded)
    print(f"Decoded type: {type(decoded).__name__}")
    print(f"  From entry: {decoded.from_entry}")
    print(f"  To entry: {decoded.to_entry}")
    print()


if __name__ == "__main__":
    example_read_by_range()
    example_read_by_entry_basic()
    example_read_by_entry_column_filtering()
    example_parser_with_column_filter()
    example_parse_entries_with_range()
    example_combined_approach()
    example_access_descriptor_factory()

    print("\n=== Key Takeaways ===")
    print("1. ReadByRange: Filter by time range (uses RangeDescriptor)")
    print("2. ReadByEntry: Filter by entry index (uses EntryDescriptor)")
    print("3. Column filtering reduces data transfer and processing")
    print("4. Use combined approach for maximum efficiency")
    print("5. Parser can filter columns after data retrieval")
    print("\nBest practices:")
    print("- Use ReadByRange when you need specific time periods")
    print("- Use ReadByEntry with column filtering for large profiles")
    print("- Combine both for optimal performance")
    print("- Always verify capture_objects match your meter's configuration")
