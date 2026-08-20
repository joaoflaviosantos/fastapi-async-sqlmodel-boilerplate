# Built-in Dependencies
from datetime import timedelta
from unittest.mock import AsyncMock, patch

# Third-Party Dependencies
import pytest
import jwt
from jwt import InvalidTokenError

# Local Dependencies
from src.core.security import (
    ALGORITHM,
    SECRET_KEY,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)

pytestmark = pytest.mark.unit


async def test_password_hash_roundtrip() -> None:
    hashed = get_password_hash("Str1ngst!")
    assert await verify_password("Str1ngst!", hashed) is True
    assert await verify_password("wrong-pass", hashed) is False


async def test_authenticate_user_by_email_and_username() -> None:
    db_user = {"username": "admin", "hashed_password": get_password_hash("Str1ngst!")}
    with patch("src.core.security.user_repository") as repo:
        repo.get = AsyncMock(return_value=db_user)
        by_email = await authenticate_user("admin@tester.com", "Str1ngst!", db=object())
        by_name = await authenticate_user("admin", "Str1ngst!", db=object())

    assert by_email == db_user
    assert by_name == db_user


async def test_authenticate_user_unknown_and_wrong_password() -> None:
    with patch("src.core.security.user_repository") as repo:
        repo.get = AsyncMock(return_value=None)
        assert await authenticate_user("nobody", "x", db=object()) is False

    hashed = get_password_hash("Str1ngst!")
    with patch("src.core.security.user_repository") as repo:
        repo.get = AsyncMock(return_value={"hashed_password": hashed})
        assert await authenticate_user("admin", "wrong-pass", db=object()) is False


async def test_create_tokens_with_and_without_expiry() -> None:
    access = await create_access_token({"sub": "admin"})
    access_exp = await create_access_token({"sub": "admin"}, expires_delta=timedelta(minutes=1))
    refresh = await create_refresh_token({"sub": "admin"})
    refresh_exp = await create_refresh_token({"sub": "admin"}, expires_delta=timedelta(days=1))
    assert access
    assert access_exp
    assert refresh
    assert refresh_exp
    assert jwt.decode(access, SECRET_KEY, algorithms=[ALGORITHM])["typ"] == TOKEN_TYPE_ACCESS
    assert jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])["typ"] == TOKEN_TYPE_REFRESH


async def test_verify_token_blacklisted_and_invalid() -> None:
    with patch("src.core.security.token_blacklist_repository") as repo:
        repo.exists = AsyncMock(return_value=True)
        assert await verify_token("tok", db=object(), expected_type="access") is None

    with patch("src.core.security.token_blacklist_repository") as repo:
        repo.exists = AsyncMock(return_value=False)
        with patch("src.core.security.jwt.decode", side_effect=InvalidTokenError("bad")):
            assert await verify_token("tok", db=object(), expected_type="access") is None


async def test_verify_token_rejects_wrong_typ() -> None:
    access = await create_access_token({"sub": "admin"})
    refresh = await create_refresh_token({"sub": "admin"})
    with patch("src.core.security.token_blacklist_repository") as repo:
        repo.exists = AsyncMock(return_value=False)
        with patch("src.core.security.user_repository") as user_repo:
            user_repo.get = AsyncMock()
            assert await verify_token(access, db=object(), expected_type="refresh") is None
            assert await verify_token(refresh, db=object(), expected_type="access") is None
            user_repo.get.assert_not_awaited()


async def test_verify_token_accepts_matching_typ() -> None:
    access = await create_access_token({"sub": "admin"})
    user = {"username": "admin"}
    with patch("src.core.security.token_blacklist_repository") as repo:
        repo.exists = AsyncMock(return_value=False)
        with patch("src.core.security.cache") as cache_module:
            cache_module.client = None
            with patch("src.core.security.user_repository") as user_repo:
                user_repo.get = AsyncMock(return_value=user)
                token_data = await verify_token(access, db=object(), expected_type="access")

    assert token_data is not None
    assert token_data.username_or_email == "admin"
