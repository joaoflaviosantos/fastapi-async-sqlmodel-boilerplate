# Built-in Dependencies
from typing import Annotated, Union, Any

# Third-Party Dependencies
from fastapi import Depends, HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.system.auth.services import AuthService, auth_service
from src.apps.system.users.repositories import user_repository
from src.core.db.session import async_get_db
from src.core.exceptions.http_exceptions import UnauthorizedException, ForbiddenException
from src.core.logger import logger_api
from src.core.security import oauth2_scheme, verify_token


async def get_auth_service() -> AuthService:
    return auth_service


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Union[dict[str, Any], None]:
    """
    Require a valid bearer token and return the authenticated user dict.

    Use when the handler needs the user but not a session that stamps
    ``updated_by_user_id`` (for example ``GET /system/users/me/``). For
    authenticated writes, use ``async_get_user_context_db`` instead of
    injecting this alongside ``db``.
    """
    token_data = await verify_token(token, db)
    if token_data is None:
        raise UnauthorizedException(detail="User not authenticated.")

    # Check if the authentication token represents an email or username and retrieve the user information
    if "@" in token_data.username_or_email:
        user: dict | None = await user_repository.get(
            db=db, email=token_data.username_or_email, is_active=True, is_deleted=False
        )
    else:
        user = await user_repository.get(
            db=db, username=token_data.username_or_email, is_active=True, is_deleted=False
        )

    if user:
        # Return the user information if available
        return user

    # Raise an exception if the user is not authenticated
    raise UnauthorizedException(detail="User not authenticated.")


async def get_optional_user(
    request: Request, db: AsyncSession = Depends(async_get_db)
) -> dict | None:
    """
    Return the authenticated user if a bearer token is present, else None.

    Use on public routes that change behavior when someone is logged in
    (rate limits, optional personalization). A missing or invalid token
    returns ``None``; it does not raise 401.
    """
    token = request.headers.get("Authorization")
    if not token:
        return None

    try:
        # Parse the Authorization token and verify it to obtain token data
        token_type, _, token_value = token.partition(" ")
        if token_type.lower() != "bearer" or not token_value:
            # Return None if the token is not a bearer token
            return None

        token_data = await verify_token(token_value, db)
        if token_data is None:
            # Return None if token verification fails
            return None

        # Retrieve the current user information based on the token data
        return await get_current_user(token_value, db=db)

    except HTTPException as http_exc:
        if http_exc.status_code != 401:
            # Log unexpected HTTPException with non-401 status code.
            logger_api.error(f"Unexpected HTTPException in get_optional_user: {http_exc.detail}")
        return None

    except Exception as exc:
        # Log unexpected errors during execution.
        logger_api.error(f"Unexpected error in get_optional_user: {exc}")
        return None


async def get_current_superuser(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """
    Require the current user to be a superuser.

    Use as ``dependencies=[Depends(get_current_superuser)]`` on privileged
    routes (hard delete ``/db``, admin-only lists). Raises 403 otherwise.
    """
    if not current_user["is_superuser"]:
        raise ForbiddenException(detail="You do not have enough privileges.")

    return current_user


async def async_get_user_context_db(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> AsyncSession:
    """
    Return the DB session with ``current_user`` attached.

    Use as the **sole** auth and session dependency on authenticated writes
    (``write_*``, ``patch_*``, ``erase_*``) so ``RepositoryBase.update`` /
    ``.delete`` stamp ``updated_by_user_id``. Do not also inject
    ``Depends(get_current_user)`` on the same handler.

    Read the user in the handler with::

        current_user = getattr(db, "current_user", {})
    """
    setattr(db, "current_user", current_user)
    return db
