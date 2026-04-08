#!/usr/bin/env python3
"""
Exception Handling Example

This example demonstrates how to handle errors and exceptions
when working with DLMS/COSEM devices.

The exception hierarchy allows you to:
1. Catch all DLMS errors with a single base exception
2. Handle specific error types differently
3. Access error codes and context for programmatic responses
4. Provide user-friendly error messages
"""
from datetime import datetime

from dlms_cosem import cosem, enumerations
from dlms_cosem.exceptions import (
    ApplicationAssociationError,
    DlmsConnectionError as DlmsConnectionError,
    DlmsException,
    DlmsProtocolError,
    DlmsSecurityError,
    DlmsErrorCode,
    InvalidSecuritySuiteError,
    TimeoutError as DlmsTimeoutError,
    CommunicationError as DlmsCommunicationError,
    create_connection_error,
    create_security_error,
    create_timeout_error,
)


def example_basic_exception_handling():
    """
    Example 1: Basic exception handling.

    Catch all DLMS exceptions using the base DlmsException class.
    """
    print("=== Example 1: Basic Exception Handling ===\n")

    def read_meter_data(client, attribute):
        """Simulated function that might raise exceptions."""
        # This would normally call: client.get(attribute)
        pass

    # Best practice: catch DlmsException to handle all DLMS errors
    try:
        # Simulated client operation
        print("Attempting to read meter data...")
        # In real code: data = client.get(attribute)
    except DlmsException as e:
        print(f"DLMS Error occurred: {e.message}")
        if e.error_code is not None:
            print(f"  Error code: {e.error_code}")
    print()


def example_specific_exception_types():
    """
    Example 2: Handling specific exception types.

    Different error types may require different handling strategies.
    """
    print("=== Example 2: Specific Exception Types ===\n")

    def handle_connection_error():
        """Handle connection-related errors."""
        try:
            # Simulate connection attempt
            raise DlmsConnectionError("Failed to connect to meter")
        except DlmsConnectionError as e:
            print(f"Connection error: {e.message}")
            # Connection errors might be transient - retry logic
            print("  Action: Retry connection")
            print("  Action: Check meter is powered on")
            print("  Action: Verify network connectivity")

    def handle_security_error():
        """Handle security-related errors."""
        try:
            # Simulate security error
            raise InvalidSecuritySuiteError("Invalid security suite: 99")
        except DlmsSecurityError as e:
            print(f"Security error: {e.message}")
            # Security errors require configuration changes
            print("  Action: Check security suite configuration")
            print("  Action: Verify key lengths")
            print("  Action: Check authentication settings")

    def handle_protocol_error():
        """Handle protocol-related errors."""
        try:
            # Simulate protocol error
            raise DlmsProtocolError("Conformance error: feature not supported")
        except DlmsProtocolError as e:
            print(f"Protocol error: {e.message}")
            # Protocol errors indicate configuration mismatch
            print("  Action: Check conformance settings")
            print("  Action: Verify meter capabilities")
            print("  Action: Update client configuration")

    handle_connection_error()
    print()
    handle_security_error()
    print()
    handle_protocol_error()
    print()


def example_error_codes():
    """
    Example 3: Using error codes for programmatic handling.

    Error codes allow you to programmatically respond to errors
    without parsing error messages.
    """
    print("=== Example 3: Error Code Handling ===\n")

    from dlms_cosem.exceptions import DlmsErrorCode

    # Define error handling strategies based on error codes
    ERROR_ACTIONS = {
        DlmsErrorCode.TIMEOUT_ERROR: "retry_with_backoff",
        DlmsErrorCode.CONNECTION_ERROR: "retry_immediate",
        DlmsErrorCode.DECRYPTION_ERROR: "check_credentials",
        DlmsErrorCode.CONFORMANCE_ERROR: "update_configuration",
    }

    def handle_by_error_code(exception):
        """Handle exception based on error code."""
        if exception.error_code in ERROR_ACTIONS:
            action = ERROR_ACTIONS[exception.error_code]
            print(f"Error {exception.error_code}: {action}")
            return action
        else:
            print(f"Error {exception.error_code}: unknown_action")
            return "log_and_continue"

    # Simulate different errors
    errors = [
        DlmsTimeoutError("Connection timed out", DlmsErrorCode.TIMEOUT_ERROR),
        DlmsConnectionError("Connection refused", DlmsErrorCode.CONNECTION_ERROR),
    ]

    for error in errors:
        action = handle_by_error_code(error)
        print(f"  Action: {action}")
    print()


def example_factory_functions():
    """
    Example 4: Using factory functions to create detailed errors.

    Factory functions allow you to create exceptions with
    additional context and suggestions.
    """
    print("=== Example 4: Factory Functions ===\n")

    # Create timeout error with context
    timeout_error = create_timeout_error(
        "Meter response timeout",
        timeout_seconds=30.0,
    )

    print(f"Timeout error: {timeout_error.message}")
    print(f"  Context: {timeout_error.context}")
    print()

    # Create security error with suggestion
    security_error = create_security_error(
        "Decryption failed",
        error_code=2004,  # DECRYPTION_ERROR
        suggestion="Verify encryption key matches meter configuration",
    )

    print(f"Security error: {security_error.message}")
    print(f"  Suggestion: {security_error.suggestion}")
    print()


def example_nested_exception_handling():
    """
    Example 5: Nested exception handling.

    Handle specific exceptions first, then fall back to
    more general handlers.
    """
    print("=== Example 5: Nested Exception Handling ===\n")

    exceptions_to_test = [
        DlmsCommunicationError("Network error"),
        DlmsTimeoutError("Operation timed out"),
        ValueError("Non-DLMS error"),
    ]

    for exc in exceptions_to_test:
        try:
            raise exc
        except DlmsTimeoutError as e:
            # Handle timeout specifically
            print(f"Timeout: {e.message} -> Retry with backoff")
        except DlmsConnectionError as e:
            # Handle all connection errors
            print(f"Connection: {e.message} -> Check connection")
        except DlmsException as e:
            # Handle all other DLMS errors
            print(f"DLMS: {e.message} -> Log and investigate")
        except Exception as e:
            # Handle non-DLMS errors
            print(f"General: {type(e).__name__} -> Unexpected error")
    print()


def example_contextual_error_handling():
    """
    Example 6: Contextual error handling with retry logic.

    Different error types may warrant different retry strategies.
    """
    print("=== Example 6: Contextual Error Handling ===\n")

    class SmartClient:
        """Example client with smart error handling."""

        def __init__(self, max_retries=3):
            self.max_retries = max_retries
            self.retry_count = 0

        def read_with_retry(self, attribute):
            """Read from meter with automatic retry logic."""

            while self.retry_count < self.max_retries:
                try:
                    # Simulate read operation
                    print(f"Attempt {self.retry_count + 1}...")
                    # In real code: return client.get(attribute)
                    break
                except DlmsTimeoutError as e:
                    # Timeout: retry with exponential backoff
                    self.retry_count += 1
                    wait_time = 2 ** self.retry_count
                    print(f"  Timeout: {e.message}")
                    print(f"  Retrying in {wait_time} seconds...")
                    if self.retry_count >= self.max_retries:
                        raise Exception("Max retries exceeded") from e
                except ApplicationAssociationError as e:
                    # Association error: don't retry
                    print(f"  Association error: {e.message}")
                    print(f"  Not retryable - check configuration")
                    raise e
                except DlmsSecurityError as e:
                    # Security error: don't retry
                    print(f"  Security error: {e.message}")
                    print(f"  Not retryable - check credentials")
                    raise e
                except DlmsConnectionError as e:
                    # Other connection errors: retry immediately
                    self.retry_count += 1
                    print(f"  Connection error: {e.message}")
                    print(f"  Retrying immediately...")
                    if self.retry_count >= self.max_retries:
                        raise Exception("Max retries exceeded") from e

    client = SmartClient(max_retries=3)
    # In real code: client.read_with_retry(attribute)
    print("(Simulated retry logic)")
    print()


def example_error_recovery_suggestions():
    """
    Example 7: Error recovery suggestions.

    Provide helpful suggestions for common error scenarios.
    """
    print("=== Example 7: Error Recovery Suggestions ===\n")

    ERROR_SUGGESTIONS = {
        "timeout": [
            "Check network connectivity",
            "Verify meter is powered on",
            "Increase timeout value",
            "Check for network congestion",
        ],
        "authentication": [
            "Verify authentication credentials",
            "Check password/key is correct",
            "Ensure HLS method is supported",
            "Check security suite matches meter",
        ],
        "conformance": [
            "Check meter's conformance settings",
            "Verify requested features are supported",
            "Update client conformance settings",
            "Consult meter's conformance EDL",
        ],
    }

    def get_suggestions(error_type):
        """Get recovery suggestions for an error type."""
        return ERROR_SUGGESTIONS.get(error_type, ["Check logs for details"])

    print("Suggestions for common errors:")
    for error_type in ["timeout", "authentication", "conformance"]:
        print(f"\n{error_type.upper()}:")
        for suggestion in get_suggestions(error_type):
            print(f"  - {suggestion}")
    print()


def example_user_friendly_error_messages():
    """
    Example 8: Creating user-friendly error messages.

    Transform technical errors into user-friendly messages.
    """
    print("=== Example 8: User-Friendly Error Messages ===\n")

    def translate_error_to_user_message(error: DlmsException) -> str:
        """Translate technical error to user-friendly message."""

        if isinstance(error, DlmsTimeoutError):
            return "The meter didn't respond in time. Please check if the meter is powered on and connected to the network."

        if isinstance(error, InvalidSecuritySuiteError):
            return "The security configuration doesn't match the meter. Please check the encryption settings in your configuration."

        if isinstance(error, ApplicationAssociationError):
            return "Failed to establish a connection with the meter. Please verify the meter's address and your access credentials."

        if isinstance(error, DlmsProtocolError):
            return "The meter doesn't support this operation. Please check if your meter has the required features."

        # Default generic message
        return f"An error occurred while communicating with the meter: {error.message}"

    # Simulate different errors
    errors = [
        DlmsTimeoutError("Connection timeout after 30s", DlmsErrorCode.TIMEOUT_ERROR),
        InvalidSecuritySuiteError("Invalid security suite: 99"),
        ApplicationAssociationError("Association rejected"),
        DlmsProtocolError("Feature not supported"),
    ]

    for error in errors:
        user_message = translate_error_to_user_message(error)
        print(f"Technical: {error.message}")
        print(f"User message: {user_message}")
        print()


if __name__ == "__main__":
    example_basic_exception_handling()
    example_specific_exception_types()
    example_error_codes()
    example_factory_functions()
    example_nested_exception_handling()
    example_contextual_error_handling()
    example_error_recovery_suggestions()
    example_user_friendly_error_messages()

    print("\n=== Key Takeaways ===")
    print("1. Use DlmsException to catch all DLMS errors")
    print("2. Handle specific error types with appropriate responses")
    print("3. Use error codes for programmatic error handling")
    print("4. Provide context and suggestions with factory functions")
    print("5. Implement retry logic for transient errors")
    print("6. Translate technical errors into user-friendly messages")
    print("\nBest practices:")
    print("- Log all exceptions with full context")
    print("- Implement retry logic for timeout/connection errors")
    print("- Don't retry security/authentication errors")
    print("- Provide actionable error messages to users")
    print("- Use error codes to trigger specific handling")
