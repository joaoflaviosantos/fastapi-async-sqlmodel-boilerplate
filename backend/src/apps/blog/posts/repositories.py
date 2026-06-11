# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.blog.posts.models import Post
from src.apps.blog.posts.schemas import (
    PostCreateInternal,
    PostUpdate,
    PostUpdateInternal,
    PostDelete,
)

# Define Repository operations for the 'Post' model
PostRepository = RepositoryBase[
    Post, PostCreateInternal, PostUpdate, PostUpdateInternal, PostDelete
]

# Create an instance of PostRepository for the 'Post' model
post_repository = PostRepository(Post)
