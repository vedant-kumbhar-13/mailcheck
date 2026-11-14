from email_validator import EmailNotValidError, validate_email


def check_syntax(address: str) -> tuple[bool, str]:
    """
    Returns (is_valid, normalized_or_original).
    Uses email-validator with check_deliverability=False.
    """
    try:
        info = validate_email(address, check_deliverability=False)
        return True, info.normalized
    except EmailNotValidError:
        return False, address
