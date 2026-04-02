#!/usr/bin/env python3
"""
dlms-keys - Command-line tool for DLMS/COSEM key management.

This tool provides utilities for:
- Generating encryption keys for DLMS/COSEM security
- Validating key configurations
- Rotating keys
- Converting between key formats

Usage:
    dlms-keys generate --suite 0 --output keys.toml
    dlms-keys validate --file keys.toml
    dlms-keys rotate --file keys.toml --keep-backup
    dlms-keys convert --input keys.toml --output keys.yaml --format yaml
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from dlms_cosem.key_management import (
    KeyManager,
    SecurityProfile,
    SecuritySuiteNumber,
    KeyFormat,
)
from dlms_cosem.key_management.key_storage import FileStorage


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate new keys for a security suite."""
    suite = args.suite  # Use int directly

    if suite not in [0, 1, 2]:
        print(f"Error: Invalid security suite: {suite}")
        print("Valid suites: 0, 1, 2")
        return 1

    print(f"Generating keys for Security Suite {suite}...")

    profile = KeyManager.generate(
        suite=suite,
        name=args.name or "default",
        system_title=args.system_title,
    )

    output_path = Path(args.output) if args.output else None

    if output_path:
        KeyManager.save(profile, str(output_path))
        print(f"Keys saved to: {output_path}")
    else:
        # Print to stdout
        print("\n" + "=" * 60)
        print("Generated Security Profile")
        print("=" * 60)
        suite_name = {0: "AES-128-GCM", 1: "AES-128-GCM", 2: "AES-256-GCM"}.get(suite, "Unknown")
        print(f"Suite: {suite} ({suite_name})")
        print(f"System Title: {profile.system_title.hex() if profile.system_title else 'N/A'}")
        print(f"Encryption Key: {profile.encryption_key.hex() if profile.encryption_key else 'N/A'}")
        print(f"Authentication Key: {profile.authentication_key.hex() if profile.authentication_key else 'N/A'}")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a key configuration file."""
    config_path = Path(args.file)

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    try:
        storage = FileStorage(str(config_path))
        # Try to load with common profile names
        profile_names = ["default", "keys", "main"]
        profile = None

        for name in profile_names:
            try:
                profile = storage.load(name)
                break
            except Exception:
                continue

        if profile is None:
            # Try to load from file structure directly
            import tomli
            with open(config_path, "rb") as f:
                data = tomli.load(f)
            # Get first profile name
            first_name = list(data.keys())[0]
            profile = storage.load(first_name)

        print(f"✓ Configuration is valid: {config_path}")
        print(f"  Profile: {profile.name}")
        print(f"  Suite: {profile.suite}")
        print(f"  System Title: {profile.system_title.hex() if profile.system_title else 'N/A'}")
        return 0
    except Exception as e:
        print(f"✗ Configuration is invalid: {e}")
        return 1


def cmd_rotate(args: argparse.Namespace) -> int:
    """Rotate keys in a configuration file."""
    config_path = Path(args.file)

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    try:
        storage = FileStorage(str(config_path))
        # Find the profile name
        import tomli
        with open(config_path, "rb") as f:
            data = tomli.load(f)
        profile_name = list(data.keys())[0]
        old_profile = storage.load(profile_name)

        # Generate new keys
        new_profile = KeyManager.generate(
            suite=old_profile.suite,
            name=old_profile.name,
            system_title=old_profile.system_title,
        )

        # Create backup if requested
        if args.keep_backup:
            backup_path = config_path.with_suffix(f".bak.{config_path.suffix}")
            import shutil
            shutil.copy2(config_path, backup_path)
            print(f"Backup saved to: {backup_path}")

        # Save new keys
        KeyManager.save(new_profile, str(config_path))
        print(f"Keys rotated successfully: {config_path}")
        print(f"  New encryption key: {new_profile.encryption_key.hex()[:16]}...")

        return 0
    except Exception as e:
        print(f"Error rotating keys: {e}")
        return 1


def cmd_convert(args: argparse.Namespace) -> int:
    """Convert key configuration between formats."""
    from dlms_cosem.key_management.formatters import KeyFormatter

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    try:
        # Load the profile
        import tomli
        storage = FileStorage(str(input_path))
        with open(input_path, "rb") as f:
            data = tomli.load(f)
        profile_name = list(data.keys())[0]
        profile = storage.load(profile_name)

        # Determine output format
        output_format = args.format or output_path.suffix.lstrip('.')
        format_map = {
            'toml': KeyFormat.TOML,
            'yaml': KeyFormat.YAML,
            'env': KeyFormat.ENV,
            'json': KeyFormat.JSON,
        }

        if output_format not in format_map:
            print(f"Error: Unsupported output format: {output_format}")
            print(f"Supported formats: {', '.join(format_map.keys())}")
            return 1

        # Convert and save
        KeyManager.save(profile, str(output_path), format_map[output_format])
        print(f"Converted: {input_path} -> {output_path}")

        return 0
    except Exception as e:
        print(f"Error converting configuration: {e}")
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Display information about a configuration file."""
    config_path = Path(args.file)

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    try:
        storage = FileStorage(str(config_path))
        # Find the profile name
        import tomli
        with open(config_path, "rb") as f:
            data = tomli.load(f)
        profile_name = list(data.keys())[0]
        profile = storage.load(profile_name)

        print("\n" + "=" * 60)
        print("Security Profile Information")
        print("=" * 60)
        print(f"File: {config_path}")
        print(f"Name: {profile.name}")
        suite_name = {0: "AES-128-GCM", 1: "AES-128-GCM", 2: "AES-256-GCM"}.get(profile.suite, "Unknown")
        print(f"Suite: {profile.suite} ({suite_name})")
        print(f"System Title: {profile.system_title.hex() if profile.system_title else 'N/A'}")
        print(f"\nKeys:")
        print(f"  Encryption: {profile.encryption_key.hex() if profile.encryption_key else 'N/A'}")
        print(f"  Authentication: {profile.authentication_key.hex() if profile.authentication_key else 'N/A'}")
        print(f"\nKey Lengths:")
        if profile.encryption_key:
            print(f"  Encryption: {len(profile.encryption_key) * 8} bits")
        if profile.authentication_key:
            print(f"  Authentication: {len(profile.authentication_key) * 8} bits")
        print()

        return 0
    except Exception as e:
        print(f"Error reading configuration: {e}")
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="dlms-keys",
        description="DLMS/COSEM key management utility",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate new keys")
    generate_parser.add_argument(
        "--suite", "-s",
        type=int,
        required=True,
        choices=[0, 1, 2],
        help="Security suite number (0, 1, or 2)",
    )
    generate_parser.add_argument(
        "--output", "-o",
        help="Output file path (TOML, YAML, or ENV format)",
    )
    generate_parser.add_argument(
        "--name", "-n",
        default="default",
        help="Profile name (default: default)",
    )
    generate_parser.add_argument(
        "--system-title",
        help="System title (hex string, auto-generated if not provided)",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate key configuration")
    validate_parser.add_argument(
        "--file", "-f",
        required=True,
        help="Configuration file to validate",
    )

    # Rotate command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate keys in configuration")
    rotate_parser.add_argument(
        "--file", "-f",
        required=True,
        help="Configuration file to update",
    )
    rotate_parser.add_argument(
        "--keep-backup",
        action="store_true",
        help="Keep a backup of the old configuration",
    )

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert configuration format")
    convert_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input configuration file",
    )
    convert_parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output configuration file",
    )
    convert_parser.add_argument(
        "--format", "-f",
        choices=["toml", "yaml", "env", "json"],
        help="Output format (auto-detected from extension if not specified)",
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Display configuration information")
    info_parser.add_argument(
        "--file", "-f",
        required=True,
        help="Configuration file to inspect",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    commands = {
        "generate": cmd_generate,
        "validate": cmd_validate,
        "rotate": cmd_rotate,
        "convert": cmd_convert,
        "info": cmd_info,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Error: Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
