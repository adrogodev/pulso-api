"""Domain errors. They carry a stable machine code; the API layer maps them to HTTP statuses."""


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class InvalidInputError(DomainError):
    code = "INVALID_INPUT"


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class PrivateContentError(DomainError):
    code = "CONTENT_PRIVATE"


class ContentRestrictedError(DomainError):
    """Age or region restricted content."""

    code = "CONTENT_RESTRICTED"


class UpstreamUnavailableError(DomainError):
    code = "UPSTREAM_UNAVAILABLE"


class UpstreamBlockedError(DomainError):
    """Upstream refused to serve this server (bot check, throttling)."""

    code = "UPSTREAM_BLOCKED"


class UpstreamTimeoutError(DomainError):
    code = "UPSTREAM_TIMEOUT"


class StreamConfigurationError(DomainError):
    """The server's streaming settings are unusable (e.g. a missing cookies file); fixed by the operator."""

    code = "STREAM_MISCONFIGURED"
