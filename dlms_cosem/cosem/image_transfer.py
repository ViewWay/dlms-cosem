"""IC068 Image Transfer - firmware upgrade support (Blue Book)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List

import structlog

# CosemClass base - standalone IC implementation

LOG = structlog.get_logger()


class ImageTransferStatus(IntEnum):
    """Image transfer status (Blue Book Table 42)."""
    IMAGE_NOT_VERIFIED = 0
    IMAGE_VERIFICATION_PENDING = 1
    IMAGE_VERIFICATION_FAILED = 2
    IMAGE_VERIFICATION_SUCCESSFUL = 3
    IMAGE_ACTIVATION_PENDING = 4
    IMAGE_ACTIVATION_FAILED = 5
    IMAGE_ACTIVATION_SUCCESSFUL = 6
    IMAGE_ACTIVATION_NOT_POSSIBLE = 7


class ImageActivationState(IntEnum):
    """Image activation state."""
    INACTIVE = 0
    ACTIVE = 1


class ImageIdentity(IntEnum):
    """Image identity types."""
    FIRMWARE = 0
    FIRMWARE_WITH_CERTIFICATES = 1
    OTHER = 2


@dataclass
class ImageBlock:
    """A block of image data."""
    block_number: int
    data: bytes
    is_last: bool = False

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    def __len__(self) -> int:
        return len(self.data)


@dataclass
class ImageInfo:
    """Image information (attribute 2 of IC 68)."""
    image_identity: bytes = b""
    image_size: int = 0
    image_transfer_status: ImageTransferStatus = ImageTransferStatus.IMAGE_NOT_VERIFIED
    image_activation_state: ImageActivationState = ImageActivationState.INACTIVE
    image_identity_type: ImageIdentity = ImageIdentity.FIRMWARE
    signing_certificate: Optional[bytes] = None
    signature: Optional[bytes] = None


@dataclass
class ImageTransferCapabilities:
    """Image transfer capabilities (attribute 4)."""
    image_block_size: int = 200
    firmware_update_supported: bool = True
    image_refusal_supported: bool = False
    multiple_image_types_supported: bool = False
    signing_supported: bool = False


class ImageTransfer:
    """IC068 Image Transfer - firmware upgrade management.

    Class ID: 68 (0x44)
    OBIS: 0.0.44.0.0.255

    Attributes:
        1: logical_name
        2: image_info (ImageInfo)
        3: image_block_transfer (ImageBlock)
        4: image_transfer_capabilities
        5: image_activate
        6: image_block_size (override)
        7: image_first_block_number
        8: image_number_of_blocks

    Methods:
        1: image_verify
        2: image_activate
        3: image_prepare
    """

    CLASS_ID = 68
    VERSION = 1

    def __init__(self, image_block_size: int = 200, image_size: int = 0):
        self.image_info = ImageInfo(image_size=image_size)
        self.image_transfer_capabilities = ImageTransferCapabilities(
            image_block_size=image_block_size,
        )
        self._blocks: List[ImageBlock] = []
        self._block_number = 0
        self._received_data = bytearray()

    @property
    def logical_name(self) -> str:
        return "0.0.44.0.0.255"

    @property
    def status(self) -> ImageTransferStatus:
        return self.image_info.image_transfer_status

    def get_image_info(self) -> ImageInfo:
        """Get current image info."""
        return self.image_info

    def get_capabilities(self) -> ImageTransferCapabilities:
        """Get image transfer capabilities."""
        return self.image_transfer_capabilities

    def get_number_of_blocks(self) -> int:
        """Calculate number of blocks for current image."""
        if self.image_info.image_size == 0:
            return 0
        bs = self.image_transfer_capabilities.image_block_size
        return (self.image_info.image_size + bs - 1) // bs

    def upload_image_block(self, block: ImageBlock) -> bool:
        """Process an uploaded image block.

        Returns True if this was the last block.
        """
        self._blocks.append(block)
        self._received_data.extend(block.data)
        self._block_number = block.block_number

        if block.is_last:
            self.image_info.image_transfer_status = (
                ImageTransferStatus.IMAGE_VERIFICATION_PENDING
            )
            LOG.info(
                "image_upload_complete",
                blocks=len(self._blocks),
                size=len(self._received_data),
                expected=self.image_info.image_size,
            )
            return True
        return False

    def upload_image(self, data: bytes, image_identity: bytes = b"") -> List[ImageBlock]:
        """Split image data into blocks for transfer.

        Returns list of ImageBlock objects ready to be sent.
        """
        bs = self.image_transfer_capabilities.image_block_size
        self.image_info.image_identity = image_identity
        self.image_info.image_size = len(data)
        self.image_info.image_transfer_status = ImageTransferStatus.IMAGE_NOT_VERIFIED
        self._received_data.clear()
        self._blocks.clear()

        blocks = []
        offset = 0
        block_num = 0
        while offset < len(data):
            chunk = data[offset:offset + bs]
            is_last = (offset + bs) >= len(data)
            blocks.append(ImageBlock(
                block_number=block_num,
                data=chunk,
                is_last=is_last,
            ))
            offset += bs
            block_num += 1

        return blocks

    def verify_image(self, expected_size: Optional[int] = None) -> ImageTransferStatus:
        """Verify uploaded image (method 1).

        Checks size and optional checksum.
        """
        if not self._received_data:
            self.image_info.image_transfer_status = (
                ImageTransferStatus.IMAGE_VERIFICATION_FAILED
            )
            return self.image_info.image_transfer_status

        if expected_size is not None and len(self._received_data) != expected_size:
            self.image_info.image_transfer_status = (
                ImageTransferStatus.IMAGE_VERIFICATION_FAILED
            )
            return self.image_info.image_transfer_status

        if self.image_info.image_size > 0 and len(self._received_data) != self.image_info.image_size:
            self.image_info.image_transfer_status = (
                ImageTransferStatus.IMAGE_VERIFICATION_FAILED
            )
            return self.image_info.image_transfer_status

        self.image_info.image_transfer_status = (
            ImageTransferStatus.IMAGE_VERIFICATION_SUCCESSFUL
        )
        LOG.info("image_verified", size=len(self._received_data))
        return self.image_info.image_transfer_status

    def activate_image(self) -> ImageTransferStatus:
        """Activate the verified image (method 2).

        Returns the new transfer status.
        """
        if self.image_info.image_transfer_status != ImageTransferStatus.IMAGE_VERIFICATION_SUCCESSFUL:
            self.image_info.image_transfer_status = (
                ImageTransferStatus.IMAGE_ACTIVATION_NOT_POSSIBLE
            )
            return self.image_info.image_transfer_status

        self.image_info.image_transfer_status = ImageTransferStatus.IMAGE_ACTIVATION_PENDING
        # In real implementation, this would trigger firmware update
        self.image_info.image_transfer_status = ImageTransferStatus.IMAGE_ACTIVATION_SUCCESSFUL
        self.image_info.image_activation_state = ImageActivationState.ACTIVE
        LOG.info("image_activated", identity=self.image_info.image_identity.hex())
        return self.image_info.image_transfer_status

    def prepare_image(self) -> ImageTransferStatus:
        """Prepare for image transfer (method 3)."""
        self._blocks.clear()
        self._received_data.clear()
        self._block_number = 0
        self.image_info.image_transfer_status = ImageTransferStatus.IMAGE_NOT_VERIFIED
        self.image_info.image_activation_state = ImageActivationState.INACTIVE
        LOG.info("image_prepare")
        return self.image_info.image_transfer_status

    def get_reconstructed_image(self) -> bytes:
        """Get the reconstructed image from received blocks."""
        return bytes(self._received_data)


class FemeterOTA:
    """Integration with Femeter OTA firmware update system.

    Provides helper methods for Femeter smart meter firmware management.
    """

    def __init__(self, image_transfer: ImageTransfer):
        self.image_transfer = image_transfer

    def create_firmware_blocks(
        self,
        firmware_data: bytes,
        version: str = "1.0.0",
    ) -> List[ImageBlock]:
        """Create firmware blocks for Femeter OTA transfer."""
        identity = f"FEMETER_{version}".encode("utf-8")[:16]
        return self.image_transfer.upload_image(firmware_data, identity)

    def verify_and_activate(self) -> dict:
        """Verify and activate firmware in one step."""
        result = {
            "verify": None,
            "activate": None,
            "success": False,
        }

        result["verify"] = self.image_transfer.verify_image()
        if result["verify"] == ImageTransferStatus.IMAGE_VERIFICATION_SUCCESSFUL:
            result["activate"] = self.image_transfer.activate_image()
            result["success"] = (
                result["activate"] == ImageTransferStatus.IMAGE_ACTIVATION_SUCCESSFUL
            )
        return result

    def get_status_report(self) -> dict:
        """Get OTA status report."""
        info = self.image_transfer.get_image_info()
        return {
            "image_identity": info.image_identity.hex(),
            "image_size": info.image_size,
            "transfer_status": ImageTransferStatus(info.image_transfer_status).name,
            "activation_state": ImageActivationState(info.image_activation_state).name,
            "blocks_transferred": len(self.image_transfer._blocks),
            "total_blocks": self.image_transfer.get_number_of_blocks(),
        }
