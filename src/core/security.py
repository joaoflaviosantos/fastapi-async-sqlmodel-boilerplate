# Built-in Dependencies
from typing import Union, Literal, Dict, Any
from datetime import datetime, timedelta

# Third-Party Dependencies
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import bcrypt

# Local Dependencies
from src.core.common.schemas import TokenData, TokenBlacklistCreate
from src.core.db.crud_token_blacklist import crud_token_blacklist
from src.apps.system.users.crud import crud_users
from src.core.config import settings

# Constants for token-related settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# OAuth2PasswordBearer instance for handling token retrieval from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/system/auth/login")

# Function to verify plain password against hashed password
async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# Function to generate hashed password from plain password
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Function to authenticate a user based on provided credentials
async def authenticate_user(username_or_email: str, password: str, db: AsyncSession) -> Union[Dict[str, Any], Literal[False]]:
    if "@" in username_or_email:
        db_user: dict | None = await crud_users.get(db=db, email=username_or_email, is_deleted=False)
    else:
        db_user = await crud_users.get(db=db, username=username_or_email, is_deleted=False)
    
    if not db_user:
        return False
    
    elif not await verify_password(password, db_user["hashed_password"]):
        return False
    
    return db_user

# Function to create an access token with optional expiration time
async def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to create a refresh token with optional expiration time
async def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to verify the validity of a token and return TokenData if valid
async def verify_token(token: str, db: AsyncSession) -> TokenData | None:
    """
    Verify a JWT token and return TokenData if valid.

    Parameters
    ----------
    token: str 
        The JWT token to be verified.
    db: AsyncSession 
        Database session for performing database operations.

    Returns
    -------
    TokenData | None
        TokenData instance if the token is valid, None otherwise.
    """
    is_blacklisted = await crud_token_blacklist.exists(db, token=token)
    if is_blacklisted:
        return None

    try:
        # Decode the token payload and extract the subject (username or email)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username_or_email: str = payload.get("sub")
        if username_or_email is None:
            return None
        return TokenData(username_or_email=username_or_email)
    
    except JWTError:
        return None

# Function to blacklist a token by storing it in the database
async def blacklist_token(token: str, db: AsyncSession) -> None:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expires_at = datetime.fromtimestamp(payload.get("exp"))
    await crud_token_blacklist.create(
        db,
        object=TokenBlacklistCreate(
            **{"token": token, "expires_at": expires_at}
        )
    )
