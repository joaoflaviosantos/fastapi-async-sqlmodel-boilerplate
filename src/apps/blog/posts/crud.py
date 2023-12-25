from src.core.common.crud import CRUDBase
from src.apps.blog.posts.models import Post
from src.apps.blog.posts.schemas import PostCreateInternal, PostUpdate, PostUpdateInternal, PostDelete

CRUDPost = CRUDBase[Post, PostCreateInternal, PostUpdate, PostUpdateInternal, PostDelete]
crud_posts = CRUDPost(Post)
