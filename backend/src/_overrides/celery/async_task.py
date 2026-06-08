# Built-in Dependencies
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar
from functools import wraps
from asgiref import sync

# Third-Party Dependencies
from celery import Celery, Task

_P = ParamSpec("_P")
_R = TypeVar("_R")


# https://stackoverflow.com/a/75437648
def async_task(app: Celery, *args: Any, **kwargs: Any):
    def _decorator(func: Callable[_P, Coroutine[Any, Any, _R]]) -> Task:
        sync_call = sync.AsyncToSync(func)

        @app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return sync_call(*args, **kwargs)

        return _decorated

    return _decorator
