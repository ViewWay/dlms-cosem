import pytest

from dlms_cosem import cosem, enumerations
from dlms_cosem.protocol import xdlms


class TestSetRequestNormal:
    def test_transform_bytes(self):
        data = b"\xc1\x01\xc1\x00\x08\x00\x00\x01\x00\x00\xff\x02\x00\t\x0c\x07\xe5\x01\x18\xff\x0e09P\xff\xc4\x00"
        request = xdlms.SetRequestNormal(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=255),
                attribute=2,
            ),
            data=b"\t\x0c\x07\xe5\x01\x18\xff\x0e09P\xff\xc4\x00",
            access_selection=None,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(
                invoke_id=1, confirmed=True, high_priority=True
            ),
        )
        assert data == request.to_bytes()
        assert request == xdlms.SetRequestNormal.from_bytes(data)

    def test_wrong_tag_raises_value_error(self):
        data = b"\xc2\x01\xc1\x00\x08\x00\x00\x01\x00\x00\xff\x02\x00\t\x0c\x07\xe5\x01\x18\xff\x0e09P\xff\xc4\x00"
        with pytest.raises(ValueError):
            xdlms.SetRequestNormal.from_bytes(data)

    def test_wrong_type_raises_value_error(self):

        data = b"\xc1\x02\xc1\x00\x08\x00\x00\x01\x00\x00\xff\x02\x00\t\x0c\x07\xe5\x01\x18\xff\x0e09P\xff\xc4\x00"
        with pytest.raises(ValueError):
            xdlms.SetRequestNormal.from_bytes(data)


class TestSetRequestFactory:
    def test_set_request_normal(self):
        data = b"\xc1\x01\xc1\x00\x08\x00\x00\x01\x00\x00\xff\x02\x00\t\x0c\x07\xe5\x01\x18\xff\x0e09P\xff\xc4\x00"
        request = xdlms.SetRequestFactory.from_bytes(data)
        assert isinstance(request, xdlms.SetRequestNormal)

    def test_wrong_tag_raises_value_error(self):
        data = b"\xc2\x01\xc1\x00\x08\x00\x00\x01\x00\x00\xff\x02\x00\t\x0c\x07\xe5\x01\x18\xff\x0e09P\xff\xc4\x00"
        with pytest.raises(ValueError):
            xdlms.SetRequestFactory.from_bytes(data)

    def test_set_request_with_first_block(self):
        """Test SetRequestWithFirstBlock parsing."""
        request = xdlms.SetRequestWithFirstBlock(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=255),
                attribute=2,
            ),
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=0,
            data_block=b"TestData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.SetRequestWithFirstBlock)
        assert decoded.block_number == 0
        assert not decoded.last_block
        assert decoded.data_block == b"TestData"

    def test_set_request_with_block(self):
        """Test SetRequestWithBlock parsing."""
        request = xdlms.SetRequestWithBlock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=1,
            data_block=b"MoreData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.SetRequestWithBlock)
        assert decoded.block_number == 1
        assert not decoded.last_block
        assert decoded.data_block == b"MoreData"

    def test_set_request_with_list(self):
        """Test SetRequestWithList parsing."""
        attrs = [
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=1),
                attribute=2,
            ),
        ]
        values = [b"Value1"]

        request = xdlms.SetRequestWithList(
            attribute_descriptor_list=attrs,
            value_list=values,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.SetRequestWithList)
        assert len(decoded.attribute_descriptor_list) == 1
        assert len(decoded.value_list) == 1
        assert decoded.value_list[0] == b"Value1"

    def test_set_request_with_list_first_block(self):
        """Test SetRequestWithListFirstBlock parsing."""
        attrs = [
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=1),
                attribute=2,
            ),
        ]

        request = xdlms.SetRequestWithListFirstBlock(
            attribute_descriptor_list=attrs,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=0,
            data_block=b"Block1",
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.SetRequestWithListFirstBlock)
        assert len(decoded.attribute_descriptor_list) == 1
        assert not decoded.last_block
        assert decoded.block_number == 0
        assert decoded.data_block == b"Block1"


class TestSetRequestWithFirstBlock:
    def test_encode_decode(self):
        """Test encoding and decoding SetRequestWithFirstBlock."""
        request = xdlms.SetRequestWithFirstBlock(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=255),
                attribute=2,
            ),
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=0,
            data_block=b"FirstBlockData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestWithFirstBlock.from_bytes(encoded)
        assert decoded.data_block == b"FirstBlockData"
        assert decoded.block_number == 0
        assert not decoded.last_block


class TestSetRequestWithBlock:
    def test_encode_decode_last_block(self):
        """Test encoding and decoding SetRequestWithBlock with last block."""
        request = xdlms.SetRequestWithBlock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=2),
            last_block=True,
            block_number=5,
            data_block=b"LastBlockData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestWithBlock.from_bytes(encoded)
        assert decoded.data_block == b"LastBlockData"
        assert decoded.block_number == 5
        assert decoded.last_block


class TestSetRequestWithList:
    def test_encode_decode_multiple_attributes(self):
        """Test encoding and decoding SetRequestWithList with multiple attributes."""
        attrs = [
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=1),
                attribute=2,
            ),
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=2),
                attribute=2,
            ),
        ]
        values = [b"Value1", b"Value2"]

        request = xdlms.SetRequestWithList(
            attribute_descriptor_list=attrs,
            value_list=values,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=3),
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestWithList.from_bytes(encoded)
        assert len(decoded.attribute_descriptor_list) == 2
        assert len(decoded.value_list) == 2
        assert decoded.value_list[0] == b"Value1"
        assert decoded.value_list[1] == b"Value2"


class TestSetRequestWithListFirstBlock:
    def test_encode_decode(self):
        """Test encoding and decoding SetRequestWithListFirstBlock."""
        attrs = [
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(a=0, b=0, c=1, d=0, e=0, f=1),
                attribute=2,
            ),
        ]

        request = xdlms.SetRequestWithListFirstBlock(
            attribute_descriptor_list=attrs,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            last_block=False,
            block_number=0,
            data_block=b"BlockData",
        )
        encoded = request.to_bytes()
        decoded = xdlms.SetRequestWithListFirstBlock.from_bytes(encoded)
        assert len(decoded.attribute_descriptor_list) == 1
        assert decoded.data_block == b"BlockData"
        assert decoded.block_number == 0


class TestSetResponseNormal:
    def test_transform_bytes(self):
        data = b"\xc5\x01\xc1\x00"
        response = xdlms.SetResponseNormal(
            result=enumerations.DataAccessResult.SUCCESS,
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(
                invoke_id=1, confirmed=True, high_priority=True
            ),
        )
        assert data == response.to_bytes()
        assert response == xdlms.SetResponseNormal.from_bytes(data)

    def test_wrong_tag_raises_value_error(self):
        data = b"\xc6\x01\xc1\x00"
        with pytest.raises(ValueError):
            xdlms.SetRequestNormal.from_bytes(data)

    def test_wrong_type_raises_value_error(self):
        data = b"\xc5\x02\xc1\x00"
        with pytest.raises(ValueError):
            xdlms.SetRequestNormal.from_bytes(data)


class TestSetResponseFactory:
    def test_set_response_normal(self):
        data = b"\xc5\x01\xc1\x00"
        request = xdlms.SetResponseFactory.from_bytes(data)
        assert isinstance(request, xdlms.SetResponseNormal)

    def test_wrong_tag_raises_value_error(self):
        data = b"\xc6\x01\xc1\x00"
        with pytest.raises(ValueError):
            xdlms.SetResponseFactory.from_bytes(data)

    def test_set_response_with_block(self):
        """Test SetResponseWithBlock parsing."""
        response = xdlms.SetResponseWithBlock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            block_number=5,
        )
        encoded = response.to_bytes()
        decoded = xdlms.SetResponseFactory.from_bytes(encoded)
        assert isinstance(decoded, xdlms.SetResponseWithBlock)
        assert decoded.block_number == 5

    def test_set_response_last_block(self):
        """Test SetResponseLastBlock parsing."""
        data = b"\xc5\x03\xc1\x00\x00\x00\x00\x03"
        response = xdlms.SetResponseFactory.from_bytes(data)
        assert isinstance(response, xdlms.SetResponseLastBlock)
        assert response.block_number == 3
        assert response.result == enumerations.DataAccessResult.SUCCESS

    def test_set_response_last_block_with_list(self):
        """Test SetResponseLastBlockWithList parsing."""
        # Tag(1) + Type(1) + InvokeId(1) + NumResults(1) + Result1(1) + Result2(1) + BlockNum(4)
        data = b"\xc5\x04\xc1\x02\x00\x01\x00\x00\x00\x03"
        response = xdlms.SetResponseFactory.from_bytes(data)
        assert isinstance(response, xdlms.SetResponseLastBlockWithList)
        assert response.block_number == 3
        assert len(response.result_list) == 2

    def test_set_response_with_list(self):
        """Test SetResponseWithList parsing."""
        # Tag(1) + Type(1) + InvokeId(1) + NumResults(1) + Result1(1)
        data = b"\xc5\x05\xc1\x02\x00\x01"
        response = xdlms.SetResponseFactory.from_bytes(data)
        assert isinstance(response, xdlms.SetResponseWithList)
        assert len(response.result_list) == 2


class TestSetResponseWithBlock:
    def test_encode_decode(self):
        """Test encoding and decoding SetResponseWithBlock."""
        response = xdlms.SetResponseWithBlock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            block_number=10,
        )
        encoded = response.to_bytes()
        decoded = xdlms.SetResponseWithBlock.from_bytes(encoded)
        assert decoded.block_number == 10


class TestSetResponseLastBlock:
    def test_encode_decode_with_result(self):
        """Test encoding and decoding SetResponseLastBlock."""
        response = xdlms.SetResponseLastBlock(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            block_number=5,
            result=enumerations.DataAccessResult.SUCCESS,
        )
        encoded = response.to_bytes()
        decoded = xdlms.SetResponseLastBlock.from_bytes(encoded)
        assert decoded.block_number == 5
        assert decoded.result == enumerations.DataAccessResult.SUCCESS


class TestSetResponseLastBlockWithList:
    def test_encode_decode(self):
        """Test encoding and decoding SetResponseLastBlockWithList."""
        response = xdlms.SetResponseLastBlockWithList(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            block_number=3,
            result_list=[
                enumerations.DataAccessResult.SUCCESS,
                enumerations.DataAccessResult.SUCCESS,
            ],
        )
        encoded = response.to_bytes()
        decoded = xdlms.SetResponseLastBlockWithList.from_bytes(encoded)
        assert decoded.block_number == 3
        assert len(decoded.result_list) == 2


class TestSetResponseWithList:
    def test_encode_decode(self):
        """Test encoding and decoding SetResponseWithList."""
        response = xdlms.SetResponseWithList(
            invoke_id_and_priority=xdlms.InvokeIdAndPriority(invoke_id=1),
            result_list=[
                enumerations.DataAccessResult.SUCCESS,
                enumerations.DataAccessResult.SUCCESS,
                enumerations.DataAccessResult.SUCCESS,
            ],
        )
        encoded = response.to_bytes()
        decoded = xdlms.SetResponseWithList.from_bytes(encoded)
        assert len(decoded.result_list) == 3
