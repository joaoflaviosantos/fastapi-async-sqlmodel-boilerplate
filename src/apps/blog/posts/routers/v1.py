# Built-in Dependencies
from typing import Annotated, Dict
from uuid import UUID

# Third-Party Dependencies
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.apps.blog.posts.schemas import (
    PostCreate,
    PostUpdate,
    PostRead,
    PostCreateInternal,
)
from src.core.exceptions.http_exceptions import (
    NotFoundException,
    ForbiddenException,
)
from src.core.api.dependencies import get_current_user, get_current_superuser
from src.apps.system.users.schemas import UserRead
from src.apps.system.users.crud import crud_users
from src.apps.blog.posts.crud import crud_posts
from src.core.db.session import async_get_db
from src.core.utils.cache import cache
from src.core.utils.paginated import (
    PaginatedListResponse,
    paginated_response,
    compute_offset,
)

router = fastapi.APIRouter(tags=["Blog - Posts"])


@router.post("/blog/{username}/post", response_model=PostRead, status_code=201)
async def write_post(
    request: Request,
    username: str,
    post: PostCreate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> PostRead:
    db_user = await crud_users.get(
        db=db, schema_to_select=UserRead, username=username, is_deleted=False
    )
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    post_internal_dict = post.model_dump()
    post_internal_dict["user_id"] = db_user["id"]

    post_internal = PostCreateInternal(**post_internal_dict)
    return await crud_posts.create(db=db, object=post_internal)


@router.get("/blog/{username}/posts", response_model=PaginatedListResponse[PostRead])
@cache(
    key_prefix="{username}_posts:page_{page}:items_per_page:{items_per_page}",
    resource_id_name="username",
    expiration=60,
)
async def read_posts(
    request: Request,
    username: str,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    db_user = await crud_users.get(
        db=db, schema_to_select=UserRead, username=username, is_deleted=False
    )
    if not db_user:
        raise NotFoundException("User not found")

    posts_data = await crud_posts.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        schema_to_select=PostRead,
        user_id=db_user["id"],
        is_deleted=False,
    )

    return paginated_response(crud_data=posts_data, page=page, items_per_page=items_per_page)


@router.get("/blog/{username}/post/{id}", response_model=PostRead)
@cache(key_prefix="{username}_post_cache", resource_id_name="id")
async def read_post(
    request: Request,
    username: str,
    id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    db_user = await crud_users.get(
        db=db, schema_to_select=UserRead, username=username, is_deleted=False
    )
    if db_user is None:
        raise NotFoundException("User not found")

    db_post = await crud_posts.get(
        db=db,
        schema_to_select=PostRead,
        id=id,
        user_id=db_user["id"],
        is_deleted=False,
    )
    if db_post is None:
        raise NotFoundException("Post not found")

    return db_post


@router.patch("/blog/{username}/post/{id}")
@cache(
    "{username}_post_cache",
    resource_id_name="id",
    pattern_to_invalidate_extra=["{username}_posts:*"],
)
async def patch_post(
    request: Request,
    username: str,
    id: UUID,
    values: PostUpdate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, str]:
    db_user = await crud_users.get(
        db=db, schema_to_select=UserRead, username=username, is_deleted=False
    )
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    db_post = await crud_posts.get(db=db, schema_to_select=PostRead, id=id, is_deleted=False)
    if db_post is None:
        raise NotFoundException("Post not found")

    await crud_posts.update(db=db, object=values, id=id)
    return {"message": "Post updated"}


@router.delete("/blog/{username}/post/{id}")
@cache(
    "{username}_post_cache",
    resource_id_name="id",
    pattern_to_invalidate_extra=["{username}_posts:*"],
)
async def erase_post(
    request: Request,
    username: str,
    id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, str]:
    db_user = await crud_users.get(
        db=db, schema_to_select=UserRead, username=username, is_deleted=False
    )
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    db_post = await crud_posts.get(db=db, schema_to_select=PostRead, id=id, is_deleted=False)
    if db_post is None:
        raise NotFoundException("Post not found")

    await crud_posts.delete(db=db, db_row=db_post, id=id)

    return {"message": "Post deleted"}


@router.delete(
    "/blog/{username}/db_post/{id}",
    dependencies=[Depends(get_current_superuser)],
)
@cache(
    "{username}_post_cache",
    resource_id_name="id",
    pattern_to_invalidate_extra=["{username}_posts:*"],
)
async def erase_db_post(
    request: Request,
    username: str,
    id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, str]:
    db_user = await crud_users.get(
        db=db, schema_to_select=UserRead, username=username, is_deleted=False
    )
    if db_user is None:
        raise NotFoundException("User not found")

    db_post = await crud_posts.get(db=db, schema_to_select=PostRead, id=id)
    if db_post is None:
        raise NotFoundException("Post not found")

    await crud_posts.db_delete(db=db, id=id)
    return {"message": "Post deleted from the database"}
