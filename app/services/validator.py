import re
from typing import Tuple, Optional, Any, Dict

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_recipient_data(name: Optional[str], email: Optional[str] = None, custom_fields: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates recipient data.
    Returns (True, None) if valid, or (False, "error message") if invalid.
    """
    if not name or not isinstance(name, str) or not name.strip():
        return False, "Recipient name is required and cannot be blank."
    
    if len(name.strip()) < 2:
        return False, "Recipient name must be at least 2 characters long."
        
    if len(name.strip()) > 100:
        return False, "Recipient name exceeds maximum allowed length (100 characters)."

    if email and isinstance(email, str) and email.strip():
        clean_email = email.strip()
        if not EMAIL_REGEX.match(clean_email):
            return False, f"Invalid email format: '{clean_email}'."

    return True, None
