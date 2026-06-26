# Built-in Dependencies
from typing import Annotated, Dict
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.core.common.deps import get_current_user, get_current_superuser, get_post_service
from src.apps.system.users.schemas import UserRead
from src.apps.blog.posts.services import PostService
from src.core.db.session import async_get_db
from src.core.utils.cache import cache
from src.apps.blog.posts.schemas import PostCreate, PostUpdate, PostRead
from src.core.common.schemas import PaginatedListResponse

# TODO: Improve the cache strategy on composite routes. Eg: '/blog/posts/{post_id}/user/{user_id}' is not good.

router = fastapi.APIRouter(tags=["Blog - Posts"])


@router.post("/blog/posts/user/{user_id}", response_model=PostRead, status_code=201)
async def write_post(
    request: Request,
    user_id: UUID,
    post: PostCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    post_service: PostService = Depends(get_post_service),
) -> PostRead:
    return await post_service.create_post(
        db=db, user_id=user_id, post=post, current_user=current_user
    )


@router.get("/blog/posts/user/{user_id}", response_model=PaginatedListResponse[PostRead])
@cache(
    key_prefix="blog:posts:user:{user_id}:page_{page}:items_per_page:{items_per_page}",
    resource_id_name="user_id",
    expiration=60,
)
async def read_posts(
    request: Request,
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    post_service: PostService = Depends(get_post_service),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    return await post_service.get_posts(
        db=db, user_id=user_id, page=page, items_per_page=items_per_page
    )


@router.get("/blog/posts/{post_id}/user/{user_id}", response_model=PostRead)
@cache(key_prefix="blog:posts:user:{user_id}:post_cache", resource_id_name="post_id")
async def read_post(
    request: Request,
    user_id: UUID,
    post_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    post_service: PostService = Depends(get_post_service),
) -> dict:
    return await post_service.get_post(db=db, user_id=user_id, post_id=post_id)


@router.patch("/blog/posts/{post_id}/user/{user_id}")
@cache(
    "blog:posts:user:{user_id}:post_cache",
    resource_id_name="post_id",
    pattern_to_invalidate_extra=["blog:posts:user:{user_id}:*"],
)
async def patch_post(
    request: Request,
    user_id: UUID,
    post_id: UUID,
    values: PostUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    post_service: PostService = Depends(get_post_service),
) -> Dict[str, str]:
    return await post_service.update_post(
        db=db, user_id=user_id, post_id=post_id, values=values, current_user=current_user
    )


@router.delete("/blog/posts/{post_id}/user/{user_id}")
@cache(
    "blog:posts:user:{user_id}:post_cache",
    resource_id_name="post_id",
    pattern_to_invalidate_extra=["blog:posts:user:{user_id}:*"],
)
async def erase_post(
    request: Request,
    user_id: UUID,
    post_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    post_service: PostService = Depends(get_post_service),
) -> Dict[str, str]:
    return await post_service.delete_post(
        db=db, user_id=user_id, post_id=post_id, current_user=current_user
    )


@router.delete(
    "/blog/posts/{post_id}/user/{user_id}/db",
    dependencies=[Depends(get_current_superuser)],
)
@cache(
    "blog:posts:user:{user_id}:post_cache",
    resource_id_name="post_id",
    pattern_to_invalidate_extra=["blog:posts:user:{user_id}:*"],
)
async def erase_db_post(
    request: Request,
    user_id: UUID,
    post_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    post_service: PostService = Depends(get_post_service),
) -> Dict[str, str]:
    return await post_service.db_delete_post(db=db, user_id=user_id, post_id=post_id)
