# Built-in Dependencies
from typing import Optional
import unicodedata
import secrets
import string
import re


def generate_random_password(length: int = 12) -> str:
    """
    Generate a random password using letters, digits, and punctuation.

    Args:
        length: The desired password length. Defaults to 12.

    Returns:
        A randomly generated password string.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(characters) for _ in range(length))


def normalize_string(s: Optional[str]) -> Optional[str]:
    """
    Normalize a string for database storage or comparisons.

    The normalization process:
    - Converts the value to string
    - Removes accent marks
    - Converts to uppercase
    - Trims leading and trailing whitespace
    - Replaces spaces with underscores
    - Replaces non-alphanumeric characters with underscores
    - Collapses repeated underscores into a single underscore

    Args:
        s: The input string.

    Returns:
        The normalized string, or None if the input is None.
    """
    if s is None:
        return None

    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.upper().strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s
