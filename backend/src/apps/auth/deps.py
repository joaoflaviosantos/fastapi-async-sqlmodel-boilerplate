# Built-in Dependencies
from typing import Annotated, Union, Any

# Third-Party Dependencies
from fastapi import Depends, HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.auth.services import AuthService, auth_service
from src.apps.system.users.repositories import user_repository
from src.core.db.session import async_get_db
from src.core.exceptions.http_exceptions import UnauthorizedException, ForbiddenException
from src.core.logger import logger_api
from src.core.security import oauth2_scheme, verify_token


async def get_auth_service() -> AuthService:
    return auth_service


# Function to get the current user based on the provided authentication token
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Union[dict[str, Any], None]:
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


# Function to get the optional user based on the provided request
async def get_optional_user(
    request: Request, db: AsyncSession = Depends(async_get_db)
) -> dict | None:
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


# Function to get the current superuser based on the provided current user information
async def get_current_superuser(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if not current_user["is_superuser"]:
        raise ForbiddenException(detail="You do not have enough privileges.")

    return current_user
