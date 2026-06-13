# Testing Guide

## Overview

Testing is a crucial aspect of software development, ensuring that the application functions as intended and that new changes do not introduce regressions. This guide provides instructions on how users can run tests to verify the correct functionality of the application.

Our test suite is **fully asynchronous** and uses **Testcontainers** to guarantee an isolated and clean database state for every test session. When you run the tests, a temporary PostgreSQL instance is automatically spun up using Docker, seeded with base data, and torn down once the tests finish.

## Prerequisites

- **Docker**: You must have Docker installed and running on your machine (e.g., Docker Desktop or Docker Engine) for `testcontainers` to successfully spin up the isolated PostgreSQL database.

## Running Tests

To run tests for the project, follow these steps:

1. Navigate to the `backend` directory:

   ```bash
   cd backend
   ```

2. Execute the following command to run tests:

   ```bash
   poetry run pytest tests/ -v
   ```

   This command runs all the tests located in the `tests` directory with detailed output.

3. Review the test results in the terminal. Any failures or errors will be highlighted.

## Writing Tests

If you want to contribute or extend the test coverage, consider the following:

- Tests are located in the `tests` directory, organized by the structure of the `src` directory (e.g., `src/apps/system/users/tests/test_v1.py`).

- Use the [pytest](https://docs.pytest.org/en/stable/) testing framework and [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/latest/) for writing asynchronous tests.
  
- Since tests share the same session-scoped database state, **do not permanently mutate core seed data** (like the default Tier) that other tests might rely on.
  
- Use the provided `client` fixture (an `httpx.AsyncClient`) for making API requests.

- Aim to cover different aspects of your application, including unit tests, integration tests, and any other relevant scenarios.

## Continuous Integration

The project may be set up with continuous integration (CI) tools that automatically run tests upon each commit. Be sure to check the CI status for the latest test results.

By following these testing practices, you contribute to the reliability and stability of the project.

---

[Back to backend README](../backend/README.md)
