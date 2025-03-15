

class EndException(Exception):
    pass

class LoginRedirectException(Exception):
    """Raised when a response redirects to the login page."""
    pass

class VisaTypeVerificationRedirectException(Exception):
    """Raised when a response redirects to the Visa Type Verification page."""
    pass

class BadGatewayException(Exception):
    """Raised when a 502 response is encountered after retries."""
    pass

class ForbiddenException(Exception):
    """Raised when a 403 response is encountered after retries."""
    pass

class ProxyConnectionException(Exception):
    """Raised when there is an issue with the proxy connection."""
    pass