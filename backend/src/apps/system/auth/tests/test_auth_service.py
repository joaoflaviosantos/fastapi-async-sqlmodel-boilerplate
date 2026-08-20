# Built-in Dependencies
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# Third-Party Dependencies
import pytest
from jwt import InvalidTokenError

# Local Dependencies
from src.apps.system.auth.services import ACCESS_TOKEN_EXPIRE_MINUTES, AuthService
from src.core.exceptions.http_exceptions import UnauthorizedException

pytestmark = pytest.mark.unit


async def test_login_rejects_unknown_user() -> None:
    response = MagicMock()
    with patch(
        "src.apps.system.auth.services.authenticate_user",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(UnauthorizedException):
            await AuthService().login(
                username="nobody",
                password="wrong",
                response=response,
                db=object(),
            )

    response.set_cookie.assert_not_called()


async def test_login_sets_refresh_cookie_and_returns_access_token() -> None:
    response = MagicMock()
    with patch(
        "src.apps.system.auth.services.authenticate_user",
        new_callable=AsyncMock,
        return_value={"username": "admin"},
    ):
        with patch(
            "src.apps.system.auth.services.create_access_token",
            new_callable=AsyncMock,
            return_value="access-token",
        ):
            with patch(
                "src.apps.system.auth.services.create_refresh_token",
                new_callable=AsyncMock,
                return_value="refresh-token",
            ):
                result = await AuthService().login(
                    username="admin",
                    password="secret",
                    response=response,
                    db=object(),
                )

    assert result == {"access_token": "access-token", "token_type": "bearer"}
    response.set_cookie.assert_called_once()
    assert response.set_cookie.call_args.kwargs["key"] == "refresh_token"
    assert response.set_cookie.call_args.kwargs["value"] == "refresh-token"


async def test_refresh_rejects_missing_cookie() -> None:
    request = SimpleNamespace(cookies={})
    with pytest.raises(UnauthorizedException):
        await AuthService().refresh_access_token(request=request, db=object())


async def test_refresh_rejects_invalid_token() -> None:
    request = SimpleNamespace(cookies={"refresh_token": "bad-token"})
    with patch(
        "src.apps.system.auth.services.verify_token",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(UnauthorizedException):
            await AuthService().refresh_access_token(request=request, db=object())


async def test_refresh_returns_new_access_token() -> None:
    request = SimpleNamespace(cookies={"refresh_token": "refresh-token"})
    user_data = SimpleNamespace(username_or_email="admin")
    with patch(
        "src.apps.system.auth.services.verify_token",
        new_callable=AsyncMock,
        return_value=user_data,
    ):
        with patch(
            "src.apps.system.auth.services.create_access_token",
            new_callable=AsyncMock,
            return_value="new-access",
        ) as create_access:
            result = await AuthService().refresh_access_token(request=request, db=object())

    assert result == {"access_token": "new-access", "token_type": "bearer"}
    create_access.assert_awaited_once()
    assert create_access.await_args.kwargs["expires_delta"] == timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )


async def test_logout_rejects_invalid_token() -> None:
    response = MagicMock()
    with patch(
        "src.apps.system.auth.services.blacklist_token",
        new_callable=AsyncMock,
        side_effect=InvalidTokenError("bad"),
    ):
        with pytest.raises(UnauthorizedException):
            await AuthService().logout(access_token="bad", response=response, db=object())

    response.delete_cookie.assert_not_called()


async def test_logout_blacklists_token_and_clears_cookie() -> None:
    response = MagicMock()
    with patch(
        "src.apps.system.auth.services.blacklist_token",
        new_callable=AsyncMock,
    ) as blacklist:
        result = await AuthService().logout(
            access_token="access-token",
            response=response,
            db=object(),
        )

    assert result == {"message": "Logged out successfully"}
    blacklist.assert_awaited_once()
    response.delete_cookie.assert_called_once_with(key="refresh_token")
