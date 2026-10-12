"""Custom exception hierarchy."""


class OfficeToolkitError(Exception):
    """Base exception."""


class ValidationError(OfficeToolkitError):
    """Input validation failed."""


class DecodeError(OfficeToolkitError):
    """Decode/read failed."""


class ProcessingError(OfficeToolkitError):
    """Processing failed."""


class OutputError(OfficeToolkitError):
    """Output/write failed."""


class PasswordError(OfficeToolkitError):
    """Password/permission related."""


class ResourceLimitError(OfficeToolkitError):
    """Resource limit exceeded."""


class CancelledError(OfficeToolkitError):
    """Operation cancelled."""
