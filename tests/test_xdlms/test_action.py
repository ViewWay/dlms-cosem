import pytest

from dlms_cosem import cosem, enumerations
from dlms_cosem.protocol import xdlms


class TestActionRequestNormal:
    def test_transform_bytes(self):
        # Updated to include has_access_selection flag (0x00) after method
        data = b'\xc3\x01\xc0\x00\x0f\x00\x00(\x00\x00\xff\x01\x00\x01\t\x11\x10\x00\x00\x1a\x90\xe6\xd2"\x1f\xa2\xfd\x85\xee\xd6\x1a\xcc"'
        action = xdlms.ActionRequestNormal(
            cosem_method=cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=255),
                method=1,
            ),
            data=b'\t\x11\x10\x00\x00\x1a\x90\xe6\xd2"\x1f\xa2\xfd\x85\xee\xd6\x1a\xcc"',
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(
                invoke_id=0, confirmed=True, high_priority=True
            ),
        )

        assert data == action.to_bytes()
        assert action == xdlms.ActionRequestNormal.from_bytes(data)

    def test_transform_bytes_without_data(self):
        # Updated to include has_access_selection flag (0x00) after method
        data = b"\xc3\x01\xc0\x00\x0f\x00\x00(\x00\x00\xff\x01\x00\x00"
        action = xdlms.ActionRequestNormal(
            cosem_method=cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=255),
                method=1,
            ),
            data=None,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(
                invoke_id=0, confirmed=True, high_priority=True
            ),
        )

        assert data == action.to_bytes()
        assert action == xdlms.ActionRequestNormal.from_bytes(data)

    def test_wrong_tag_raises_valueerror(self):
        data = b'\xc4\x01\xc0\x00\x0f\x00\x00(\x00\x00\xff\x01\x01\t\x11\x10\x00\x00\x1a\x90\xe6\xd2"\x1f\xa2\xfd\x85\xee\xd6\x1a\xcc"'

        with pytest.raises(ValueError):
            xdlms.ActionRequestNormal.from_bytes(data)

    def test_wrong_request_type_raises_valueerror(self):
        data = b'\xc3\x02\xc0\x00\x0f\x00\x00(\x00\x00\xff\x01\x01\t\x11\x10\x00\x00\x1a\x90\xe6\xd2"\x1f\xa2\xfd\x85\xee\xd6\x1a\xcc"'

        with pytest.raises(ValueError):
            xdlms.ActionRequestNormal.from_bytes(data)


class TestActionRequestWithFirstPblock:
    def test_encode_decode(self):
        """Test encoding and decoding ActionRequestWithFirstPblock."""
        request = xdlms.ActionRequestWithFirstPblock(
            cosem_method=cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=255),
                method=1,
            ),
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=0,
            data_block=b"FirstBlockData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestWithFirstPblock.from_bytes(encoded)
        assert decoded.data_block == b"FirstBlockData"
        assert decoded.block_number == 0
        assert not decoded.last_block

    def test_last_block(self):
        """Test encoding a last block."""
        request = xdlms.ActionRequestWithFirstPblock(
            cosem_method=cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=255),
                method=1,
            ),
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=True,
            block_number=2,
            data_block=b"LastBlockData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestWithFirstPblock.from_bytes(encoded)
        assert decoded.last_block
        assert decoded.block_number == 2


class TestActionRequestNextPblock:
    def test_encode_decode(self):
        """Test encoding and decoding ActionRequestNextPblock."""
        request = xdlms.ActionRequestNextPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=2),
            block_number=5,
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestNextPblock.from_bytes(encoded)
        assert decoded.block_number == 5


class TestActionRequestWithList:
    def test_encode_decode(self):
        """Test encoding and decoding ActionRequestWithList."""
        methods = [
            cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=1),
                method=1,
            ),
            cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=2),
                method=1,
            ),
        ]

        request = xdlms.ActionRequestWithList(
            method_list=methods,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestWithList.from_bytes(encoded)
        assert len(decoded.method_list) == 2
        # method_list now contains CosemMethodWithSelectiveAccess objects
        assert decoded.method_list[0].cosem_method.instance.f == 1


class TestActionRequestWithListAndFirstPblock:
    def test_encode_decode(self):
        """Test encoding and decoding ActionRequestWithListAndFirstPblock."""
        methods = [
            cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=1),
                method=1,
            ),
        ]

        request = xdlms.ActionRequestWithListAndFirstPblock(
            method_list=methods,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=0,
            data_block=b"Block1Data",
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestWithListAndFirstPblock.from_bytes(encoded)
        assert len(decoded.method_list) == 1
        assert decoded.data_block == b"Block1Data"


class TestActionRequestFactory:
    def test_normal_with_data(self):
        # Updated to include has_access_selection flag (0x00) after method
        data = b'\xc3\x01\xc0\x00\x0f\x00\x00(\x00\x00\xff\x01\x00\x01\t\x11\x10\x00\x00\x1a\x90\xe6\xd2"\x1f\xa2\xfd\x85\xee\xd6\x1a\xcc"'
        action = xdlms.ActionRequestFactory.from_bytes(data)
        assert isinstance(action, xdlms.ActionRequestNormal)

    def test_normal_without_data(self):
        # Updated to include has_access_selection flag (0x00) after method
        data = b"\xc3\x01\xc0\x00\x0f\x00\x00(\x00\x00\xff\x01\x00\x00"
        action = xdlms.ActionRequestFactory.from_bytes(data)
        assert isinstance(action, xdlms.ActionRequestNormal)
        assert action.data is None

    def test_wrong_tag_raises_valueerror(self):
        # Updated to include has_access_selection flag (0x00) after method
        data = b"\xc4\x01\xc0\x00\x0f\x00\x00(\x00\x00\xff\x01\x00\x00"
        with pytest.raises(ValueError):
            xdlms.ActionRequestFactory.from_bytes(data)

    def test_request_with_first_pblock(self):
        """Test parsing ActionRequestWithFirstPblock."""
        request = xdlms.ActionRequestWithFirstPblock(
            cosem_method=cosem.CosemMethod(
                interface=enumerations.CosemInterface.ASSOCIATION_LN,
                instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=255),
                method=1,
            ),
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=0,
            data_block=b"BlockData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.ActionRequestWithFirstPblock)

    def test_request_next_pblock(self):
        """Test parsing ActionRequestNextPblock."""
        request = xdlms.ActionRequestNextPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=2),
            block_number=3,
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.ActionRequestNextPblock)
        assert decoded.block_number == 3

    def test_request_with_list(self):
        """Test parsing ActionRequestWithList."""
        from dlms_cosem.protocol.xdlms.action import CosemMethodWithSelectiveAccess

        request = xdlms.ActionRequestWithList(
            method_list=[
                CosemMethodWithSelectiveAccess(
                    cosem_method=cosem.CosemMethod(
                        interface=enumerations.CosemInterface.ASSOCIATION_LN,
                        instance=cosem.Obis(a=0, b=0, c=40, d=0, e=0, f=1),
                        method=1,
                    ),
                    access_selection=None,
                ),
            ],
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
        )
        encoded = request.to_bytes()
        decoded = xdlms.ActionRequestFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.ActionRequestWithList)


class TestActionResponseNormal:
    def test_transform_bytes(self):
        data = b"\xc7\x01\xc0\x00\x00"
        action = xdlms.ActionResponseNormal(
            enumerations.ActionResultStatus.SUCCESS,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(
                invoke_id=0, confirmed=True, high_priority=True
            ),
        )
        assert data == action.to_bytes()
        assert action == xdlms.ActionResponseNormal.from_bytes(data)

    def test_wrong_tag_raises_valueerror(self):
        data = b"\xc8\x01\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormal.from_bytes(data)

    def test_wrong_type_raises_valueerror(self):
        data = b"\xc7\x02\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormal.from_bytes(data)

    def test_has_data_raises_valueerror(self):
        data = b"\xc7\x01\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormal.from_bytes(data)


class TestActionResponseNormalWithData:
    def test_transform_bytes(self):
        data = b"\xc7\x01\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        action = xdlms.ActionResponseNormalWithData(
            enumerations.ActionResultStatus.SUCCESS,
            data=bytearray(
                b"\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
            ),
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(
                invoke_id=0, confirmed=True, high_priority=True
            ),
        )
        assert data == action.to_bytes()
        assert action == xdlms.ActionResponseNormalWithData.from_bytes(data)

    def test_wrong_tag_raises_valueerror(self):
        data = b"\xc8\x01\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithData.from_bytes(data)

    def test_wrong_type_raises_valueerror(self):
        data = b"\xc7\x02\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithData.from_bytes(data)

    def test_no_data_raises_valueerror(self):
        data = b"\xc7\x01\xc0\x00\x00"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithData.from_bytes(data)

    def test_holds_error_instead_of_data_raises_valueerror(self):
        data = b"\xc7\x01\xc0\x00\x01\x01\x01"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithData.from_bytes(data)


class TestActionResponseWithError:
    def test_transform_bytes(self):
        data = b"\xc7\x01\xc0\x00\x01\x01\xfa"
        action = xdlms.ActionResponseNormalWithError(
            enumerations.ActionResultStatus.SUCCESS,
            error=enumerations.DataAccessResult.OTHER_REASON,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(
                invoke_id=0, confirmed=True, high_priority=True
            ),
        )
        assert data == action.to_bytes()
        assert action == xdlms.ActionResponseNormalWithError.from_bytes(data)

    def test_wrong_tag_raises_valueerror(self):
        data = b"\xc8\x01\xc0\x00\x01\x01\xfa"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithError.from_bytes(data)

    def test_wrong_type_raises_valueerror(self):
        data = b"\xc7\x02\xc0\x00\x01\x01\xfa"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithError.from_bytes(data)

    def test_no_data_raises_valueerror(self):
        data = b"\xc7\x01\xc0\x00\x00"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithError.from_bytes(data)

    def test_holds_data_instead_of_error_raises_valueerror(self):
        data = b"\xc7\x01\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        with pytest.raises(ValueError):
            xdlms.ActionResponseNormalWithError.from_bytes(data)


class TestActionResponseWithPblock:
    def test_encode_decode(self):
        """Test encoding and decoding ActionResponseWithPblock."""
        response = xdlms.ActionResponseWithPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=2,
            data_block=b"BlockData",
        )
        encoded = response.to_bytes()
        decoded = xdlms.ActionResponseWithPblock.from_bytes(encoded)
        assert decoded.data_block == b"BlockData"
        assert decoded.block_number == 2

    def test_last_block(self):
        """Test encoding a last block response."""
        response = xdlms.ActionResponseWithPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=True,
            block_number=5,
            data_block=b"LastBlockData",
        )
        encoded = response.to_bytes()
        decoded = xdlms.ActionResponseWithPblock.from_bytes(encoded)
        assert decoded.last_block
        assert decoded.block_number == 5


class TestActionResponseNextPblock:
    def test_encode_decode(self):
        """Test encoding and decoding ActionResponseNextPblock."""
        response = xdlms.ActionResponseNextPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=True,
            block_number=10,
            data_block=b"LastBlock",
        )
        encoded = response.to_bytes()
        decoded = xdlms.ActionResponseNextPblock.from_bytes(encoded)
        assert decoded.last_block
        assert decoded.block_number == 10


class TestActionResponseLastPblock:
    def test_encode_decode(self):
        """Test encoding and decoding ActionResponseLastPblock."""
        response = xdlms.ActionResponseLastPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            block_number=15,
            data_block=b"ResponseData",
        )
        encoded = response.to_bytes()
        decoded = xdlms.ActionResponseLastPblock.from_bytes(encoded)
        assert decoded.last_block
        assert decoded.block_number == 15


class TestActionResponseFactory:
    def test_parse_action_response_normal(self):
        data = b"\xc7\x01\xc0\x00\x00"
        action = xdlms.ActionResponseFactory.from_bytes(data)
        assert isinstance(action, xdlms.ActionResponseNormal)

    def test_parse_action_response_normal_with_data(self):
        data = b"\xc7\x01\xc0\x00\x01\x00\t\x11\x10\x00\x00\x1a\xfd\xe8\x85{r\x8a4\x99\x10j\xa6e\xd1"
        action = xdlms.ActionResponseFactory.from_bytes(data)
        assert isinstance(action, xdlms.ActionResponseNormalWithData)

    def test_parse_action_response_normal_with_error(self):
        data = b"\xc7\x01\xc0\x00\x01\x01\xfa"
        action = xdlms.ActionResponseFactory.from_bytes(data)
        assert isinstance(action, xdlms.ActionResponseNormalWithError)

    def test_wrong_tag_raises_valueerror(self):
        data = b"\xc8\x01\xc0\x00\x01\x01\xfa"
        with pytest.raises(ValueError):
            xdlms.ActionResponseFactory.from_bytes(data)

    def test_response_with_pblock(self):
        """Test parsing ActionResponseWithPblock."""
        response = xdlms.ActionResponseWithPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=3,
            data_block=b"Data",
        )
        encoded = response.to_bytes()
        decoded = xdlms.ActionResponseFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.ActionResponseWithPblock)

    def test_response_next_pblock(self):
        """Test parsing ActionResponseNextPblock."""
        response = xdlms.ActionResponseNextPblock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=7,
            data_block=b"MoreData",
        )
        encoded = response.to_bytes()
        decoded = xdlms.ActionResponseFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.ActionResponseNextPblock)
