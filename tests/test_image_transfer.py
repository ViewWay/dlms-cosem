"""Tests for Image Transfer (IC068)."""
import os
import pytest

from dlms_cosem.cosem.C35_ImageTransfer import (
    ImageTransfer, ImageBlock, ImageInfo, ImageTransferStatus,
    ImageActivationState, ImageIdentity, ImageTransferCapabilities,
    FemeterOTA,
)


class TestImageBlock:
    def test_checksum(self):
        block = ImageBlock(block_number=0, data=b"hello world")
        assert block.checksum is not None
        assert len(block.checksum) == 64  # SHA256 hex

    def test_len(self):
        block = ImageBlock(block_number=0, data=b"\x00" * 100)
        assert len(block) == 100

    def test_is_last(self):
        block = ImageBlock(block_number=0, data=b"data", is_last=True)
        assert block.is_last


class TestImageInfo:
    def test_default(self):
        info = ImageInfo()
        assert info.image_transfer_status == ImageTransferStatus.IMAGE_NOT_VERIFIED
        assert info.image_activation_state == ImageActivationState.INACTIVE

    def test_custom(self):
        info = ImageInfo(
            image_identity=b"FW_1.2.3",
            image_size=1024,
            image_transfer_status=ImageTransferStatus.IMAGE_VERIFICATION_SUCCESSFUL,
        )
        assert info.image_size == 1024
        assert info.image_identity == b"FW_1.2.3"


class TestImageTransfer:
    def test_upload_image(self):
        it = ImageTransfer(image_block_size=100)
        data = os.urandom(250)
        blocks = it.upload_image(data, b"FW_1.0")

        assert len(blocks) == 3  # 100 + 100 + 50
        assert blocks[0].block_number == 0
        assert blocks[1].block_number == 1
        assert blocks[2].is_last
        assert it.image_info.image_size == 250

    def test_upload_and_reconstruct(self):
        it = ImageTransfer(image_block_size=64)
        data = b"firmware data for testing" * 5
        blocks = it.upload_image(data, b"TEST")

        received = bytearray()
        for block in blocks:
            received.extend(block.data)

        assert bytes(received) == data

    def test_block_by_block_upload(self):
        it = ImageTransfer(image_block_size=50)
        data = b"A" * 100
        blocks = it.upload_image(data)

        for block in blocks:
            is_last = it.upload_image_block(block)

        assert is_last
        assert it.status == ImageTransferStatus.IMAGE_VERIFICATION_PENDING

    def test_verify_success(self):
        it = ImageTransfer(image_block_size=50)
        data = b"B" * 100
        blocks = it.upload_image(data)
        for block in blocks:
            it.upload_image_block(block)

        status = it.verify_image()
        assert status == ImageTransferStatus.IMAGE_VERIFICATION_SUCCESSFUL

    def test_verify_size_mismatch(self):
        it = ImageTransfer(image_block_size=50)
        data = b"C" * 100
        blocks = it.upload_image(data)
        for block in blocks:
            it.upload_image_block(block)
        # Now change expected size to cause mismatch
        status = it.verify_image(expected_size=200)
        assert status == ImageTransferStatus.IMAGE_VERIFICATION_FAILED

    def test_verify_empty(self):
        it = ImageTransfer()
        status = it.verify_image()
        assert status == ImageTransferStatus.IMAGE_VERIFICATION_FAILED

    def test_activate_after_verify(self):
        it = ImageTransfer(image_block_size=50)
        data = b"D" * 100
        blocks = it.upload_image(data)
        for block in blocks:
            it.upload_image_block(block)
        it.verify_image()

        status = it.activate_image()
        assert status == ImageTransferStatus.IMAGE_ACTIVATION_SUCCESSFUL
        assert it.image_info.image_activation_state == ImageActivationState.ACTIVE

    def test_activate_without_verify(self):
        it = ImageTransfer()
        status = it.activate_image()
        assert status == ImageTransferStatus.IMAGE_ACTIVATION_NOT_POSSIBLE

    def test_prepare(self):
        it = ImageTransfer(image_block_size=50)
        data = b"E" * 100
        it.upload_image(data)

        status = it.prepare_image()
        assert status == ImageTransferStatus.IMAGE_NOT_VERIFIED
        assert it.image_info.image_activation_state == ImageActivationState.INACTIVE

    def test_get_number_of_blocks(self):
        it = ImageTransfer(image_block_size=200, image_size=500)
        assert it.get_number_of_blocks() == 3

    def test_zero_size(self):
        it = ImageTransfer()
        assert it.get_number_of_blocks() == 0

    def test_get_reconstructed_image(self):
        it = ImageTransfer(image_block_size=10)
        data = b"reconstruct_test"
        blocks = it.upload_image(data)
        for block in blocks:
            it.upload_image_block(block)

        assert it.get_reconstructed_image() == data

    def test_single_block(self):
        it = ImageTransfer(image_block_size=1000)
        data = b"small"
        blocks = it.upload_image(data)
        assert len(blocks) == 1
        assert blocks[0].is_last


class TestFemeterOTA:
    def test_create_firmware_blocks(self):
        it = ImageTransfer(image_block_size=100)
        ota = FemeterOTA(it)
        firmware = b"FEMETER_FW" * 20
        blocks = ota.create_firmware_blocks(firmware, "2.1.0")
        assert len(blocks) > 0
        assert it.image_info.image_identity == b"FEMETER_2.1.0"

    def test_verify_and_activate_success(self):
        it = ImageTransfer(image_block_size=50)
        ota = FemeterOTA(it)
        data = b"firmware" * 20
        blocks = ota.create_firmware_blocks(data)
        for block in blocks:
            it.upload_image_block(block)

        result = ota.verify_and_activate()
        assert result["success"]

    def test_verify_and_activate_fail(self):
        it = ImageTransfer()
        ota = FemeterOTA(it)
        result = ota.verify_and_activate()
        assert not result["success"]

    def test_status_report(self):
        it = ImageTransfer(image_block_size=50)
        ota = FemeterOTA(it)
        data = b"firmware" * 10
        blocks = ota.create_firmware_blocks(data, "1.0")
        for block in blocks:
            it.upload_image_block(block)

        report = ota.get_status_report()
        assert "transfer_status" in report
        assert "blocks_transferred" in report
        assert report["blocks_transferred"] > 0


class TestImageTransferCapabilities:
    def test_default(self):
        cap = ImageTransferCapabilities()
        assert cap.image_block_size == 200
        assert cap.firmware_update_supported

    def test_custom(self):
        cap = ImageTransferCapabilities(
            image_block_size=512,
            signing_supported=True,
        )
        assert cap.image_block_size == 512
        assert cap.signing_supported
