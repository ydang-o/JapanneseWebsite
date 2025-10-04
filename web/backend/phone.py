import re
from typing import Optional


_JP_LOCAL_LENGTHS = {10, 11}


def normalize_jp_phone(raw: str) -> Optional[str]:
    """Normalize a Japanese phone number to local format (leading 0, digits only).
    Accepts inputs with spaces/hyphens and +81 international prefix.
    Returns normalized digits (e.g., '09012345678') or None if invalid.
    """
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if digits.startswith("81"):
        # Convert +81X... to 0X...
        rest = digits[2:]
        if not rest:
            return None
        digits = "0" + rest
    elif digits.startswith("0"):
        pass
    else:
        # Not a Japanese format
        return None

    if len(digits) not in _JP_LOCAL_LENGTHS:
        return None
    return digits


def is_valid_jp_phone(raw: str) -> bool:
    return normalize_jp_phone(raw) is not None
