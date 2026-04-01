"""
Key rotation utilities for DLMS/COSEM security profiles.

Manages key rotation while optionally maintaining access to old keys.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dlms_cosem.key_management.key_generator import KeyGenerator
from dlms_cosem.key_management.profiles import SecurityProfile
from dlms_cosem.key_management.formatters import KeyFormatter


@dataclass
class KeyRotationResult:
    """
    Result of a key rotation operation.

    Attributes:
        old_profile: The original security profile
        new_profile: The new security profile with fresh keys
        rotation_id: Timestamp-based identifier for this rotation
        legacy_key: Dictionary containing old keys (if keep_old_keys=True)
    """

    old_profile: SecurityProfile
    new_profile: SecurityProfile
    rotation_id: str
    legacy_key: Optional[dict] = None


class KeyRotator:
    """
    Manage key rotation for DLMS/COSEM security profiles.

    Key rotation is the process of replacing existing keys with new ones
    while optionally maintaining access to old keys for decrypting historical data.
    """

    @staticmethod
    def rotate(
        profile: SecurityProfile,
        new_suite: Optional[int] = None,
        keep_old_keys: bool = False,
        same_key: bool = True,
    ) -> KeyRotationResult:
        """
        Rotate keys in a security profile.

        Generates new encryption and authentication keys. Optionally saves
        the old keys for backward compatibility.

        Args:
            profile: Current security profile
            new_suite: New security suite (None to keep current)
            keep_old_keys: Whether to preserve old keys in the result
            same_key: Whether to use same key for encryption and authentication

        Returns:
            KeyRotationResult with old and new profiles

        Example:
            >>> result = KeyRotator.rotate(profile, keep_old_keys=True)
            >>> # Save result.new_profile to your configuration
            >>> # Store result.legacy_key for decrypting old data
        """
        from dataclasses import replace

        rotation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_suite = new_suite or profile.suite

        # Generate new keys
        new_key_pair = KeyGenerator.generate_key_pair(new_suite, same_key)

        # Create new profile with same metadata but new keys
        new_profile = replace(
            profile,
            suite=new_suite,
            encryption_key=new_key_pair.encryption_key,
            authentication_key=new_key_pair.authentication_key,
        )

        # Optionally preserve old keys
        legacy_key = None
        if keep_old_keys:
            legacy_key = {
                "encryption_key": KeyFormatter.format_key(
                    profile.encryption_key, "hex"
                ),
                "authentication_key": KeyFormatter.format_key(
                    profile.authentication_key, "hex"
                ),
                "rotated_at": datetime.now().isoformat(),
                "suite": profile.suite,
            }

        return KeyRotationResult(
            old_profile=profile,
            new_profile=new_profile,
            rotation_id=rotation_id,
            legacy_key=legacy_key,
        )

    @staticmethod
    def rotate_and_save(
        profile: SecurityProfile,
        output_path: str,
        new_suite: Optional[int] = None,
        keep_old_keys: bool = False,
    ) -> KeyRotationResult:
        """
        Rotate keys and save the new profile to a file.

        Args:
            profile: Current security profile
            output_path: Path to save the rotated configuration
            new_suite: New security suite (None to keep current)
            keep_old_keys: Whether to save old keys in the file

        Returns:
            KeyRotationResult with the new profile
        """
        result = KeyRotator.rotate(profile, new_suite, keep_old_keys)

        # Save the new profile
        from dlms_cosem.key_management.key_manager import KeyManager

        KeyManager.save(result.new_profile, output_path)

        return result
