class LocalProtocolError(Exception):
    """Error in HDLC Protocol"""


class HdlcException(Exception):
    """Base class for HDLC protocol parts"""


class HdlcParsingError(HdlcException):
    """An error occurred then parsing bytes into HDLC object"""


class MissingHdlcFlags(HdlcParsingError):
    """Frame is not enclosed byt HDLC flags"""


class HdlcTimeoutError(HdlcException):
    """HDLC operation timed out after max retries (Green Book 8.4.5.6)"""
