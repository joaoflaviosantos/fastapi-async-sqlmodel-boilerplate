# Built-in Dependencies
from typing import Dict
from datetime import timedelta

# Third-party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Response, Request
from jose import JWTError

# Local Dependencies
from src.core.exceptions.http_exceptions import UnauthorizedException
from src.core.config import settings
from src.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    authenticate_user,
    create_refresh_token,
    verify_token,
    blacklist_token,
)


class AuthService:
    def __init__(self):
        pass

    async def login(
        self, username: str, password: str, response: Response, db: AsyncSession
    ) -> Dict[str, str]:
        user = await authenticate_user(username_or_email=username, password=password, db=db)
        if not user:
            raise UnauthorizedException(detail="Wrong username, email or password.")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )

        refresh_token = await create_refresh_token(data={"sub": user["username"]})
        max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=max_age,
        )

        return {"access_token": access_token, "token_type": "bearer"}

    async def refresh_access_token(self, request: Request, db: AsyncSession) -> Dict[str, str]:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise UnauthorizedException(detail="Refresh token missing.")

        user_data = await verify_token(refresh_token, db)
        if not user_data:
            raise UnauthorizedException(detail="Invalid refresh token.")

        new_access_token = await create_access_token(data={"sub": user_data.username_or_email})
        return {"access_token": new_access_token, "token_type": "bearer"}

    async def logout(
        self, access_token: str, response: Response, db: AsyncSession
    ) -> Dict[str, str]:
        try:
            await blacklist_token(token=access_token, db=db)
            response.delete_cookie(key="refresh_token")

            return {"message": "Logged out successfully"}

        except JWTError:
            raise UnauthorizedException(detail="Invalid token.")


# Module-level singleton
auth_service = AuthService()
