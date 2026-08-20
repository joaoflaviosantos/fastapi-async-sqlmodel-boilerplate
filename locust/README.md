# Load Testing — Locust

Use this when you want to **stress-test the API** with an independent [Locust](https://locust.io) suite that has its own virtual environment and dependencies, separate from the backend.

## What's included

This suite defines a single [`HttpUser`](https://docs.locust.io/en/stable/writing-a-locustfile.html#httpuser-class) (`APIUser`) that picks weighted [`TaskSet`](https://docs.locust.io/en/stable/tasksets.html) classes — see [`locustfile.py`](locustfile.py):

| Task set               | Weight | Description                                |
| ---------------------- | ------ | ------------------------------------------ |
| `PostsTasks`           | 4      | Blog CRUD (heaviest read/write workload)   |
| `UsersTasks`           | 3      | User listing and profile access            |
| `BackgroundTasksTasks` | 2      | Background task creation and status checks |
| `TiersTasks`           | 1      | Tier listing (low frequency)               |
| `AuthTasks`            | 1      | Login/logout and token refresh cycles      |

Simulated users wait between **1 and 3 seconds** between tasks ([`wait_time`](https://docs.locust.io/en/stable/writing-a-locustfile.html#wait-time-attribute)).

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Backend API running (default: `http://127.0.0.1:8000`)
- Configured `backend/.env` with a valid admin user (migrations + first admin already applied)

## Environment variables

Configuration is loaded from `backend/.env` via [`config.py`](config.py). You can also pass Locust flags such as [`--host`](https://docs.locust.io/en/stable/configuration.html):

| Variable                    | Default                 | Description             |
| --------------------------- | ----------------------- | ----------------------- |
| `LOCUST_HOST`               | `http://127.0.0.1:8000` | Target API host         |
| `USER_FIRST_ADMIN_EMAIL`    | `admin@system.com`      | Email used for login    |
| `USER_FIRST_ADMIN_PASSWORD` | `!Ch4ng3Th1sP4ssW0rd!`  | Password used for login |

Override the host from the CLI if needed:

```bash
poetry run locust --host http://your-api-host:8000
```

## How to run

### Via `setup.py` (recommended)

From the **repository root**:

```bash
python3 setup.py
```

Select option **3 - Load Testing (Locust)** (or `python setup.py locust`). The CLI installs dependencies and starts Locust for you.

### Manual setup (Web UI)

```bash
cd locust
poetry install
poetry run locust
```

Open the [web UI](https://docs.locust.io/en/stable/quickstart.html#open-up-locust-s-web-interface) at [http://localhost:8089](http://localhost:8089) and set number of users, spawn rate, and host.

### Headless mode

Run [without the web UI](https://docs.locust.io/en/stable/running-without-web-ui.html) (useful for scripts or CI):

```bash
cd locust
poetry run locust --headless -u 50 -r 10 --run-time 60s
```

- `-u 50` — peak concurrent users (`--users`)
- `-r 10` — users spawned per second (`--spawn-rate`)
- `--run-time 60s` — total duration

Full flag reference: [Configuration](https://docs.locust.io/en/stable/configuration.html).

### HTML report

```bash
cd locust
poetry run locust --headless -u 50 -r 5 --run-time 30s --html report.html
```

See [Generate a HTML report](https://docs.locust.io/en/stable/configuration.html#all-available-configuration-options) (`--html`) in the official configuration docs.

## Documentation

| Resource                                                                                   | Description                          |
| ------------------------------------------------------------------------------------------ | ------------------------------------ |
| [Locust documentation](https://docs.locust.io/en/stable/)                                  | Official docs home                   |
| [Quickstart](https://docs.locust.io/en/stable/quickstart.html)                             | First run and web UI                 |
| [Writing a locustfile](https://docs.locust.io/en/stable/writing-a-locustfile.html)         | `HttpUser`, tasks, `wait_time`       |
| [TaskSets](https://docs.locust.io/en/stable/tasksets.html)                                 | Grouping related tasks               |
| [Running without the web UI](https://docs.locust.io/en/stable/running-without-web-ui.html) | Headless / CI usage                  |
| [Configuration](https://docs.locust.io/en/stable/configuration.html)                       | CLI flags and env vars               |
| [API reference](https://docs.locust.io/en/stable/api.html)                                 | Classes and methods                  |
| [Project Locust Guide](../docs/locust-guide.md)                                            | Suite-specific details for this repo |

## Notes

- The Locust suite uses a **separate Poetry virtual environment** (`.venv` inside `locust/`) to avoid dependency conflicts with the backend.
- Some tasks **write to the database** (e.g. creating posts and sample background tasks). Prefer a non-production environment.
- Credentials come from `USER_FIRST_ADMIN_EMAIL` / `USER_FIRST_ADMIN_PASSWORD` in `backend/.env` (same vars used to create the first admin). Ensure that admin exists before running Locust.
- For extending task sets, performance baselines, and troubleshooting, see the [Locust Guide](../docs/locust-guide.md).
