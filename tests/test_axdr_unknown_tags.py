"""Test tolerance for unknown/reserved DLMS tags."""

import pytest
from dlms_cosem.dlms_data import DlmsDataFactory, DlmsDataParser, DontCareData


class TestUnknownTagFactory:
    """DlmsDataFactory should return DontCareData for unknown tags."""

    @pytest.mark.parametrize("tag", [0x07, 0x08, 0x0B, 0x0E, 0x1C, 0x28])
    def test_unknown_tag_returns_dont_care(self, tag):
        klass = DlmsDataFactory.get_data_class(tag)
        assert klass is DontCareData

    def test_known_tags_unchanged(self):
        assert DlmsDataFactory.get_data_class(0) is not DontCareData  # NullData
        assert DlmsDataFactory.get_data_class(3) is not DontCareData  # BooleanData


class TestUnknownTagParsing:
    """DlmsDataParser should parse unknown tags without error."""

    @pytest.mark.parametrize("tag", [0x07, 0x08, 0x0B, 0x0E])
    def test_parse_unknown_tag(self, tag):
        data = bytes([tag, 0x03, 0xAA, 0xBB, 0xCC])  # tag + length 3 + 3 bytes
        parser = DlmsDataParser()
        result = parser.parse(data)
        assert len(result) == 1
        assert isinstance(result[0], DontCareData)
        assert result[0].raw_bytes == b'\xaa\xbb\xcc'

    def test_parse_mixed_known_and_unknown(self):
        """Parse a structure containing known and unknown tags."""
        data = bytes([
            2, 0x03,           # structure, 3 elements
            3, 0x01,           # boolean true
            0x07, 0x02, 0xDE, 0xAD,  # unknown tag 0x07, 2 bytes
            6, 0x00, 0x00, 0x01, 0x00,  # double-long-unsigned = 256
        ])
        parser = DlmsDataParser()
        result = parser.parse(data)
        assert len(result) == 1
        struct = result[0]
        assert len(struct.value) == 3
        assert isinstance(struct.value[1], DontCareData)
