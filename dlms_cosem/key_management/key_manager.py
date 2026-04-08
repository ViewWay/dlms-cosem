"""
Unified entry point for DLMS/COSEM key management.

Provides methods for generating, loading, and saving security configurations.
Automatically searches multiple sources in priority order.
"""
import os
from pathlib import Path
from typing import Optional

from dlms_cosem.key_management.key_generator import KeyGenerator
from dlms_cosem.key_management.key_storage import (
    EnvironmentStorage,
    FileStorage,
    ConfigurationNotFoundError,
)
from dlms_cosem.key_management.profiles import SecurityProfile, SECURITY_STRATEGIES


class KeyManager:
    """
    Unified entry point for DLMS/COSEM key management.

    Provides methods for generating, loading, and saving security configurations.
    Automatically searches multiple sources in priority order.
    """

    DEFAULT_LOOKUP_PATHS = [
        ".env",
        "keys.toml",
        "keys.yaml",
        "keys.yml",
        "~/.dlms/keys.toml",
        "/etc/dlms/keys.toml",
    ]

    @staticmethod
    def generate(
        suite: int,
        name: str = "generated",
        same_key: bool = True,
        system_title: Optional[bytes] = None,
    ) -> SecurityProfile:
        """
        Generate a new security profile with random keys.

        Args:
            suite: Security suite number (0, 1, or 2)
            name: Profile name
            same_key: Use same key for encryption and authentication
            system_title: Optional system title (auto-generated if not provided)

        Returns:
            New SecurityProfile with generated keys
        """
        key_pair = KeyGenerator.generate_key_pair(suite, same_key)

        if system_title is None:
            system_title = KeyGenerator.generate_system_title()

        return SecurityProfile(
            name=name,
            suite=suite,
            encryption_key=key_pair.encryption_key,
            authentication_key=key_pair.authentication_key,
            system_title=system_title,
        )

    @classmethod
    def load(
        cls,
        profile_name: str = "default",
        paths: Optional[list[str]] = None,
    ) -> SecurityProfile:
        """
        Load a security profile from available sources.

        Search priority:
        1. Environment variables (DLMS_*)
        2. Configuration files in provided paths (or defaults)
        3. User directory (~/.dlms/)
        4. System directory (/etc/dlms/)

        Args:
            profile_name: Profile name to load from files
            paths: Custom list of paths to search

        Returns:
            Loaded SecurityProfile

        Raises:
            ConfigurationNotFoundError: If no configuration found
        """
        # 1. Try environment variables first
        try:
            return EnvironmentStorage().load(profile_name)
        except ConfigurationNotFoundError:
            pass

        # 2-4. Try configuration files
        lookup_paths = paths or cls.DEFAULT_LOOKUP_PATHS
        for path_str in lookup_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                try:
                    return FileStorage(path).load(profile_name)
                except (ConfigurationNotFoundError, Exception):
                    continue

        raise ConfigurationNotFoundError(
            f"Security profile '{profile_name}' not found. "
            f"Searched: {lookup_paths}. "
            f"Set environment variables (DLMS_SECURITY_SUITE, etc.) or create a configuration file."
        )

    @staticmethod
    def save(
        profile: SecurityProfile,
        path: str,
    ) -> None:
        """
        Save a security profile to a file.

        Args:
            profile: SecurityProfile to save
            path: Output file path
        """
        storage = FileStorage(path)
        storage.save(profile)

    @staticmethod
    def from_strategy(
        strategy_name: str,
        **overrides,
    ) -> SecurityProfile:
        """
        Create a SecurityProfile from a predefined strategy.

        Args:
            strategy_name: Strategy name ("none", "lls", "hls-gmac", "hls-suite2")
            **overrides: Fields to override (encryption_key, etc.)

        Returns:
            SecurityProfile based on the strategy

        Example:
            profile = KeyManager.from_strategy(
                "hls-gmac",
                encryption_key=my_key,
                authentication_key=my_key,
            )
        """
        if strategy_name not in SECURITY_STRATEGIES:
            available = ", ".join(SECURITY_STRATEGIES.keys())
            raise ValueError(
                f"Unknown strategy: {strategy_name}. Available: {available}"
            )

        # Get base strategy
        base = SECURITY_STRATEGIES[strategy_name]

        # Apply overrides (create new instance with replaced fields)
        from dataclasses import replace

        return replace(base, **overrides)

    @staticmethod
    def validate(profile: SecurityProfile) -> None:
        """
        Validate a security profile.

        Args:
            profile: SecurityProfile to validate

        Raises:
            KeyLengthError: If key lengths are incorrect
            InvalidSecuritySuiteError: If suite is invalid
        """
        profile.validate()
