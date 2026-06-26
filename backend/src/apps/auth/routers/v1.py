# Built-in Dependencies
from typing import Annotated, Dict

# Third-party Dependencies
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Response, Request, Depends
import fastapi

# Local Dependencies
from src.apps.auth.schemas import Token
from src.core.db.session import async_get_db
from src.core.security import oauth2_scheme
from src.apps.auth.services import AuthService
from src.core.common.deps import get_auth_service

router = fastapi.APIRouter(tags=["Authentication"])


@router.post("/system/auth/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    return await auth_service.login(
        username=form_data.username, password=form_data.password, response=response, db=db
    )


@router.post("/system/auth/refresh")
async def refresh_access_token(
    request: Request,
    db: AsyncSession = Depends(async_get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    return await auth_service.refresh_access_token(request=request, db=db)


@router.post("/system/auth/logout")
async def logout(
    response: Response,
    access_token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(async_get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    return await auth_service.logout(access_token=access_token, response=response, db=db)
