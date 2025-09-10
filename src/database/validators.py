import re

from validate_email import validate_email
from validate_email.exceptions import EmailValidationError


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lower letter.")
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r'[@$!%*?&#]', password):
        raise ValueError("Password must contain at least one special character: @, $, !, %, *, ?, #, &.")
    return password

def validate_email_address(email: str) -> str:
    try:
        is_valid = validate_email(
            email_address=email,
            check_regex=True,
            check_mx=True,
            from_address='my@from.addr.ess',
            helo_host='my.host.name',
            smtp_timeout=10,
            dns_timeout=10,
            use_blacklist=True
        )
        if not is_valid:
            raise ValueError("Email address failed validation checks.")
    except EmailValidationError as error:
        raise ValueError(str(error))
    return email
