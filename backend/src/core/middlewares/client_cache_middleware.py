# Third-Party Dependencies
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)


class ClientCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set the `Cache-Control` header for client-side caching on all responses.

    Parameters
    ----------
    app: FastAPI
        The FastAPI application instance.
    max_age: int, optional
        Duration (in seconds) for which the response should be cached. Defaults to 60 seconds.

    Attributes
    ----------
    max_age: int
        Duration (in seconds) for which the response should be cached.

    Methods
    ----------
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        Process the request and set the `Cache-Control` header in the response.

    Note
    ----
        - Authenticated requests (`Authorization` header) get `private, no-store`.
        - Unauthenticated responses use `public, max-age` for the configured duration.
    """

    def __init__(self, app: FastAPI, max_age: int = 60) -> None:
        super().__init__(app)
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process the request and set the `Cache-Control` header in the response.

        Parameters
        ----------
        request: Request
            The incoming request.
        call_next: RequestResponseEndpoint
            The next middleware or route handler in the processing chain.

        Returns
        ----------
        Response
            The response object with the `Cache-Control` header set.
        """
        response: Response = await call_next(request)
        # Authenticated responses are user-specific and must never be cached
        # as public (browsers would serve stale library/content on soft refresh).
        if request.headers.get("Authorization"):
            response.headers["Cache-Control"] = "private, no-store"
        else:
            response.headers["Cache-Control"] = f"public, max-age={self.max_age}"
        return response
