# Local Dependencies
from src.apps.blog.posts_tags_assoc.repositories import (
    PostTagAssocRepository,
    post_tag_assoc_repository,
)


class PostTagAssocService:
    def __init__(self, assoc_repo: PostTagAssocRepository):
        self.assoc_repo = assoc_repo


post_tag_assoc_service = PostTagAssocService(post_tag_assoc_repository)
