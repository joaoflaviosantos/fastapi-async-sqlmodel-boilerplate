# Third-Party Dependencies
import pytest

# Local Dependencies
from src.core.utils.string import generate_random_password, normalize_string

pytestmark = pytest.mark.unit


def test_normalize_string_strips_accents_and_spaces() -> None:
    assert normalize_string("São Paulo") == "SAO_PAULO"


def test_normalize_string_none() -> None:
    assert normalize_string(None) is None


def test_generate_random_password_default_length() -> None:
    assert len(generate_random_password()) == 12


def test_generate_random_password_custom_length() -> None:
    assert len(generate_random_password(16)) == 16
