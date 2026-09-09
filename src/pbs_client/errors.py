"""Small exception hierarchy for pbs-client."""

from urllib.error import URLError


class PBSClientError(RuntimeError):
    """Base class for errors raised by pbs-client."""


class PBSConfigurationError(PBSClientError):
    """The client configuration is incomplete or invalid."""


class PBSAPIError(PBSClientError):
    """The PBS API returned an error or an unusable response."""


class PBSTransportError(PBSAPIError):
    """The PBS API could not be reached after all transport retries."""

    def __init__(self, url: str, attempts: int, cause: Exception) -> None:
        self.url = url
        self.attempts = attempts
        self.cause = cause
        self.timed_out = _is_timeout(cause)
        detail = "timed out" if self.timed_out else "could not be reached"
        super().__init__(f"PBS API request {detail} after {attempts} attempts: {url}")


class PBSSyncError(PBSClientError):
    """A local mirror sync could not be completed."""

    def __init__(self, message: str, *, resource: str | None = None) -> None:
        self.resource = resource
        super().__init__(message)


def _is_timeout(error: Exception) -> bool:
    """Return whether *error* represents a socket/read timeout."""

    return isinstance(error, TimeoutError) or (
        isinstance(error, URLError) and isinstance(error.reason, TimeoutError)
    )
