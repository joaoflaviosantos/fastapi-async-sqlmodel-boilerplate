# Built-in Dependencies
import asyncio
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar
from functools import wraps

# Third-Party Dependencies
from celery import Celery, Task

_P = ParamSpec("_P")
_R = TypeVar("_R")


def async_task(app: Celery, *args: Any, **kwargs: Any):
    """
    Decorator that turns an async function into a synchronous Celery task.

    Uses ``asyncio.run()`` instead of ``asgiref.AsyncToSync`` so that every
    task invocation gets its own *fresh*, isolated event loop.  This prevents
    the classic "Future attached to a different loop" / "Event loop is closed"
    errors that arise when async Redis (or any other async I/O) resources
    initialised in one loop are later accessed from a different loop.
    """

    def _decorator(func: Callable[_P, Coroutine[Any, Any, _R]]) -> Task:
        @app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return asyncio.run(func(*args, **kwargs))

        return _decorated

    return _decorator
