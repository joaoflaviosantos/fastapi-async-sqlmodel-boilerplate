# Built-in Dependencies
from datetime import datetime, timedelta, UTC
from typing import Union, Literal, Dict, Any
from uuid import uuid4

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError
import bcrypt

# Local Dependencies
from src.apps.system.auth.schemas import TokenData, TokenBlacklistCreate
from src.apps.system.auth.repositories import token_blacklist_repository
from src.apps.system.users.repositories import user_repository
from src.core.config import settings
from src.core.utils import cache

# Constants for token-related settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
TOKEN_TYPE_ACCESS: Literal["access"] = "access"
TOKEN_TYPE_REFRESH: Literal["refresh"] = "refresh"

# OAuth2PasswordBearer instance for handling token retrieval from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/system/auth/login")


# Function to verify plain password against hashed password
async def verify_password(plain_password: str, hashed_password: str) -> bool:
    correct_password: bool = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    return correct_password


# Function to generate hashed password from plain password
def get_password_hash(password: str) -> str:
    hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashed_password


# Function to authenticate a user based on provided credentials
async def authenticate_user(
    username_or_email: str, password: str, db: AsyncSession
) -> Union[Dict[str, Any], Literal[False]]:
    if "@" in username_or_email:
        db_user = await user_repository.get(db=db, email=username_or_email, is_deleted=False)
    else:
        db_user = await user_repository.get(db=db, username=username_or_email, is_deleted=False)

    if not db_user:
        return False

    elif not await verify_password(password, db_user["hashed_password"]):
        return False

    return db_user


# Function to create an access token with optional expiration time
async def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    # Aware clock for iat (naive .timestamp() is local-time on Windows).
    now_utc = datetime.now(UTC)
    now = now_utc.replace(tzinfo=None)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": str(uuid4()), "typ": TOKEN_TYPE_ACCESS})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to create a refresh token with optional expiration time
async def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    # Aware clock for iat (naive .timestamp() is local-time on Windows).
    now_utc = datetime.now(UTC)
    now = now_utc.replace(tzinfo=None)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": str(uuid4()), "typ": TOKEN_TYPE_REFRESH})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to verify the validity of a token and return TokenData if valid
async def verify_token(
    token: str,
    db: AsyncSession,
    expected_type: Literal["access", "refresh"],
) -> TokenData | None:
    """
    Verify a JWT token and return TokenData if valid.

    Parameters
    ----------
    token: str
        The JWT token to be verified.
    db: AsyncSession
        Database session for performing database operations.
    expected_type: Literal["access", "refresh"]
        Required payload ``typ`` claim. Access tokens must not be accepted
        where a refresh token is required, and the reverse.

    Returns
    ----------
    TokenData | None
        An instance of TokenData representing the user if the token is valid.
        None is returned if the token is invalid or the user is not active.
    """
    is_blacklisted = await token_blacklist_repository.exists(db, token=token)
    if is_blacklisted:
        return None

    try:
        # Decode the token payload and extract the subject (username or email)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("typ") != expected_type:
            return None

        username_or_email: str | None = payload.get("sub")
        if username_or_email is None:
            return None

        # Check if the Redis client is available
        if cache.client:
            # Check if user is active in Redis
            is_active = await cache.client.hget(
                settings.REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES,
                username_or_email,
            )

            if is_active:
                return TokenData(username_or_email=username_or_email)

        # If not active in Redis or Redis is not available, check PostgreSQL
        user = await user_repository.get(db=db, username=username_or_email, is_deleted=False)

        if user:
            # Update Redis with user active status if Redis is available
            if cache.client:
                await cache.client.hset(
                    settings.REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES,
                    username_or_email,
                    "active",
                )

            return TokenData(username_or_email=username_or_email)

        # If user is not found in Redis or PostgreSQL, blacklist the token
        await blacklist_token(token=token, db=db)

        return None

    except InvalidTokenError:
        return None


# Function to blacklist a token by storing it in the database
async def blacklist_token(token: str, db: AsyncSession) -> None:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expires_at = datetime.fromtimestamp(payload.get("exp"))
    await token_blacklist_repository.create(
        db,
        object=TokenBlacklistCreate(**{"token": token, "expires_at": expires_at}),
    )
