# Built-in Dependencies
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Third-Party Dependencies
import pytest
from celery import states
from src.core.exceptions.http_exceptions import NotFoundException

# Local Dependencies
from src.apps.system.tasks.schemas import Job, TaskRead
from src.apps.system.tasks.services import TaskService

pytestmark = pytest.mark.unit


def _task_repo() -> MagicMock:
    repo = MagicMock()
    repo.apply_filtering.side_effect = lambda stmt, **kwargs: stmt
    repo.apply_sorting.side_effect = lambda stmt, sort_by=None: stmt
    repo.read_by_task_id = AsyncMock(return_value=None)
    return repo


async def test_create_sample_shared_task_returns_job() -> None:
    fake_result = MagicMock()
    fake_result.id = "celery-job-id"
    service = TaskService(task_repo=_task_repo())

    with patch(
        "src.apps.system.tasks.services.sample_background_task.apply_async",
        return_value=fake_result,
    ):
        job = await service.create_sample_shared_task("hello")

    assert isinstance(job, Job)
    assert job.id == "celery-job-id"


async def test_get_processed_tasks_returns_paginated_dict() -> None:
    service = TaskService(task_repo=_task_repo())
    session = AsyncMock()
    count_result = MagicMock()
    count_result.one.return_value = 0
    list_result = MagicMock()
    list_result.all.return_value = []
    session.exec.side_effect = [count_result, list_result]

    result = await service.get_processed_tasks(session=session)

    assert result["data"] == []
    assert result["total_count"] == 0
    assert session.exec.await_count == 2


async def test_get_pending_tasks_returns_task_reads() -> None:
    service = TaskService(task_repo=_task_repo())
    session = AsyncMock()
    list_result = MagicMock()
    list_result.all.return_value = []
    session.exec.return_value = list_result

    result = await service.get_pending_tasks(session=session)

    assert result == []
    session.exec.assert_awaited_once()


async def test_get_queue_health_returns_counts() -> None:
    service = TaskService(task_repo=_task_repo())
    queue = SimpleNamespace(message_count=3, consumer_count=2)
    channel = MagicMock()
    channel.queue_declare.return_value = queue
    conn = MagicMock()
    conn.default_channel = channel
    cm = MagicMock()
    cm.__enter__.return_value = conn
    cm.__exit__.return_value = False

    with patch("src.apps.system.tasks.services.celery_app") as celery_app:
        celery_app.amqp.queues = {"celery": object()}
        celery_app.connection_or_acquire.return_value = cm
        result = service.get_queue_health("celery")

    assert result == {"queue_name": "celery", "message_count": 3, "consumer_count": 2}


async def test_get_queue_health_uses_inspect_when_consumer_count_is_zero() -> None:
    service = TaskService(task_repo=_task_repo())
    queue = SimpleNamespace(message_count=1, consumer_count=0)
    channel = MagicMock()
    channel.queue_declare.return_value = queue
    conn = MagicMock()
    conn.default_channel = channel
    cm = MagicMock()
    cm.__enter__.return_value = conn
    cm.__exit__.return_value = False
    inspect = MagicMock()
    inspect.active_queues.return_value = {
        "worker-1": [{"name": "celery"}],
    }
    inspect.stats.return_value = {"worker-1": {"pool": {"max-concurrency": 4}}}

    with patch("src.apps.system.tasks.services.celery_app") as celery_app:
        celery_app.amqp.queues = {"celery": object()}
        celery_app.connection_or_acquire.return_value = cm
        celery_app.control.inspect.return_value = inspect
        result = service.get_queue_health("celery")

    assert result["consumer_count"] == 4
    assert result["message_count"] == 1


async def test_get_queue_health_raises_when_broker_errors() -> None:
    service = TaskService(task_repo=_task_repo())

    with patch("src.apps.system.tasks.services.celery_app") as celery_app:
        celery_app.amqp.queues = {}
        celery_app.connection_or_acquire.side_effect = RuntimeError("no broker")
        with pytest.raises(NotFoundException) as exc_info:
            service.get_queue_health("missing")

    assert exc_info.value.status_code == 404


async def test_get_task_returns_pending_from_celery() -> None:
    service = TaskService(task_repo=_task_repo())
    job = MagicMock()
    job.state = states.PENDING

    with patch("src.apps.system.tasks.services.AsyncResult", return_value=job):
        result = await service.get_task(session=object(), task_id="pending-id")

    assert isinstance(result, TaskRead)
    assert result.task_id == "pending-id"
    assert result.status == states.PENDING


async def test_get_task_returns_database_row() -> None:
    task_repo = _task_repo()
    task_repo.read_by_task_id.return_value = SimpleNamespace(
        id=1,
        task_id="done-id",
        status=states.SUCCESS,
        name="sample",
        worker="w1",
        queue="celery",
        retries=0,
        result=None,
        traceback=None,
        date_done=None,
    )
    service = TaskService(task_repo=task_repo)
    job = MagicMock()
    job.state = states.SUCCESS

    with patch("src.apps.system.tasks.services.AsyncResult", return_value=job):
        result = await service.get_task(session=object(), task_id="done-id")

    assert result.task_id == "done-id"
    assert result.status == states.SUCCESS
    assert result.name == "sample"
    task_repo.read_by_task_id.assert_awaited_once()


async def test_get_task_falls_back_to_celery_when_database_lookup_fails() -> None:
    task_repo = _task_repo()
    task_repo.read_by_task_id.side_effect = RuntimeError("db down")
    service = TaskService(task_repo=task_repo)
    job = MagicMock()
    job.state = states.SUCCESS
    job.status = states.SUCCESS
    job.name = "sample"

    with patch("src.apps.system.tasks.services.AsyncResult", return_value=job):
        result = await service.get_task(session=object(), task_id="fallback-id")

    assert result.task_id == "fallback-id"
    assert result.status == states.SUCCESS
    assert result.name == "sample"


async def test_get_task_uses_pending_when_celery_backend_has_no_status() -> None:
    task_repo = _task_repo()
    task_repo.read_by_task_id.return_value = None
    service = TaskService(task_repo=task_repo)

    class _Job:
        @property
        def state(self) -> str:
            raise AttributeError

        @property
        def status(self) -> str:
            raise AttributeError

        name = "unused"

    with patch("src.apps.system.tasks.services.AsyncResult", return_value=_Job()):
        result = await service.get_task(session=object(), task_id="no-backend")

    assert result.task_id == "no-backend"
    assert result.status == states.PENDING


async def test_get_task_attribute_error_on_state_then_database() -> None:
    task_id = str(uuid4())
    task_repo = _task_repo()
    task_repo.read_by_task_id.return_value = SimpleNamespace(
        id=2,
        task_id=task_id,
        status=states.FAILURE,
        name="sample",
        worker=None,
        queue=None,
        retries=None,
        result=None,
        traceback=None,
        date_done=None,
    )
    service = TaskService(task_repo=task_repo)

    class _Job:
        @property
        def state(self) -> str:
            raise AttributeError

        status = states.FAILURE
        name = "sample"

    with patch("src.apps.system.tasks.services.AsyncResult", return_value=_Job()):
        result = await service.get_task(session=object(), task_id=task_id)

    assert result.status == states.FAILURE
    assert result.task_id == task_id
