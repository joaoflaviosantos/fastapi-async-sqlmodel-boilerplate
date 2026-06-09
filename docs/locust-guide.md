# 🦗 Locust Load Testing Guide

This project includes an independent **Locust** load testing suite located in the `locust/` directory. It has its own virtual environment and dependencies, completely separate from the backend application.

## 📋 Overview

[Locust](https://locust.io) is an open-source load testing tool that allows you to define user behavior in Python code and simulate thousands of concurrent users hitting your API.

The load testing suite covers the following API areas:

| Task Set               | Weight | Description                                |
| ---------------------- | ------ | ------------------------------------------ |
| `PostsTasks`           | 4      | Blog CRUD operations (heaviest workload)   |
| `UsersTasks`           | 3      | User listing and profile access            |
| `BackgroundTasksTasks` | 2      | Background task creation and status checks |
| `TiersTasks`           | 1      | Tier listing (low frequency)               |
| `AuthTasks`            | 1      | Login/logout cycles                        |

## 📁 Project Structure

```
locust/
├── config.py          # Configuration (host, credentials, API prefix)
├── helpers.py         # Shared utilities (login, token management)
├── locustfile.py      # Main entry point - defines the simulated user
├── poetry.toml        # Poetry local configuration
├── pyproject.toml     # Dependencies (independent from backend)
└── tasks/
    ├── __init__.py    # Exports all task sets
    ├── auth.py        # Authentication task set
    ├── posts.py       # Blog posts task set
    ├── tasks.py       # Background tasks task set
    ├── tiers.py       # Tiers task set
    └── users.py       # Users task set
```

## 📋 Prerequisites

- **Python 3.11+** installed
- **Poetry** installed (`pip install poetry==1.7.1`)
- The **backend API** running (default: `http://127.0.0.1:8000`)
- A configured `backend/.env` file (Locust reads credentials from it)

## 🚀 Quick Start

### Using the Project CLI

From the **root project directory**, run:

```bash
python3 setup.py
```

Select option **3 - Load Testing (Locust)** and the CLI will handle the setup and execution automatically.

### Manual Setup

1. Navigate to the `locust/` directory:

```bash
cd locust
```

2. Install dependencies (creates an independent `.venv`):

```bash
poetry install
```

3. Run Locust:

```bash
poetry run locust
```

4. Open the Locust web UI at [http://localhost:8089](http://localhost:8089).

## ⚙️ Configuration

The `locust/config.py` file reads configuration from environment variables (loaded from `backend/.env`):

| Variable         | Default                 | Description                       |
| ---------------- | ----------------------- | --------------------------------- |
| `LOCUST_HOST`    | `http://127.0.0.1:8000` | Target API host                   |
| `ADMIN_EMAIL`    | `admin@admin.com`       | Admin email for authentication    |
| `ADMIN_PASSWORD` | `admin`                 | Admin password for authentication |

### Overriding Configuration

You can override the target host directly when running Locust:

```bash
poetry run locust --host http://your-api-host:8000
```

## 🎯 Running Tests

### Web UI Mode (Default)

```bash
poetry run locust
```

Access [http://localhost:8089](http://localhost:8089) and configure:

- **Number of users** (peak concurrency)
- **Spawn rate** (users started per second)
- **Host** (target URL, pre-filled from config)

### Headless Mode (CLI)

Run without the web UI for CI/CD pipelines:

```bash
poetry run locust --headless -u 100 -r 10 --run-time 60s
```

Options:

- `-u 100`: Simulate 100 concurrent users
- `-r 10`: Spawn 10 users per second
- `--run-time 60s`: Run for 60 seconds

### Generating HTML Reports

```bash
poetry run locust --headless -u 50 -r 5 --run-time 30s --html report.html
```

## 🔧 Adding New Task Sets

1. Create a new file in `locust/tasks/` (e.g., `my_feature.py`):

```python
from locust import TaskSet, task

class MyFeatureTasks(TaskSet):
    @task
    def my_endpoint(self):
        self.client.get("/api/v1/my-feature")
```

2. Export it in `locust/tasks/__init__.py`:

```python
from .my_feature import MyFeatureTasks
```

3. Add it to `locustfile.py` with a weight:

```python
tasks = {
    # ...existing tasks...
    MyFeatureTasks: 2,
}
```

## 📊 Interpreting Results

Key metrics to monitor:

- **RPS (Requests Per Second):** Throughput of your API
- **Response Time (median/p95/p99):** Latency distribution
- **Failure Rate:** Percentage of failed requests
- **Number of Users:** Current concurrent users

### Performance Baselines

| Metric            | Acceptable       | Warning    | Critical |
| ----------------- | ---------------- | ---------- | -------- |
| p95 Response Time | < 500ms          | 500ms - 2s | > 2s     |
| Failure Rate      | < 1%             | 1% - 5%    | > 5%     |
| RPS               | Depends on infra | -          | -        |

## 🐛 Troubleshooting

### Connection Refused

Ensure the backend API is running before starting Locust:

```bash
# From the backend directory
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Authentication Failures

Verify that `backend/.env` contains valid `ADMIN_EMAIL` and `ADMIN_PASSWORD` values and that the admin user has been created (run migrations first).

### Module Not Found

Make sure you're running from the `locust/` directory and have installed dependencies:

```bash
cd locust
poetry install
```

## 📝 Notes

- The Locust suite uses a **separate virtual environment** from the backend to avoid dependency conflicts.
- Configuration is loaded from `backend/.env` so you don't need to duplicate credentials.
- The `wait_time = between(1, 3)` in `locustfile.py` simulates realistic user think time between requests.
