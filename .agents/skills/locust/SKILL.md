---
name: locust
description: Create or change Locust load-test TaskSets under locust/. Use when adding API load coverage, locustfile weights, or locust/tasks/*.py. Independent venv from the backend.
---

# Locust load tests

Reference: `locust/tasks/posts.py`, `locust/locustfile.py`, `locust/helpers.py`. Guide: `docs/locust-guide.md`.

The suite lives in `locust/` with its **own** Poetry env. Do not add Locust to `backend/`. Copy an existing TaskSet instead of inventing a new layout.

## Layout

```
locust/
  config.py          # HOST, admin credentials from backend/.env, API_V1_PREFIX
  helpers.py         # login, auth_headers, log_error
  locustfile.py      # APIUser + TaskSet weights
  tasks/
    auth.py, users.py, tiers.py, posts.py, tasks.py
```

## Add a TaskSet

1. New file `locust/tasks/<resource>.py` — `TaskSet`, `@task` weights, three import blocks.
2. Login in `on_start` via `login(self.client)`; send `auth_headers(self.access_token)`.
3. Paths use `API_V1_PREFIX` (`/api/v1`) plus the real route (`/blog/posts/...`). Set `name=` so Locust groups by template, not by UUID.
4. Export in `locust/tasks/__init__.py` and add a weight on `APIUser.tasks` in `locustfile.py`.

```python
class CommentsTasks(TaskSet):
    access_token: str = ""

    def on_start(self) -> None:
        self.access_token = login(self.client)

    @task(2)
    def list_comments(self) -> None:
        self.client.get(
            f"{API_V1_PREFIX}/blog/comments",
            headers=auth_headers(self.access_token),
            name="/blog/comments [list]",
        )
```

Treat expected 404 during concurrent CRUD as success (`catch_response=True`), same as `posts.py`.

## Run (from `locust/`)

```bash
poetry install
poetry run locust
```

API must already be up. Host defaults to `LOCUST_HOST` / `http://127.0.0.1:8000`.

## Do not

- Do not put load tests under `backend/src/apps/.../tests/` (that is pytest).
- Do not duplicate admin credentials; read `backend/.env` via `config.py`.
- Do not omit `name=` on requests with path IDs (stats explode).
