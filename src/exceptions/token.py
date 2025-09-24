class TokenExpiredError(Exception):
    """Base exception for token exired errors."""
    pass

class InvalidTokenError(Exception):
    """Base exception for invalid token errors."""
    pass
