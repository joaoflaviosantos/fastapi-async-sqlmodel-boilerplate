# Pre-Commit

Hooks in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) run **before** `git commit`. They are local (`language: system`) and call Poetry inside `backend/`. Python 3.11.

They catch format, lint, and unit-test failures on your machine so the GitHub Actions job `checks` is less of a surprise. They are **not** the full CI suite.

## What runs

On every commit (including commits that only touch markdown):

| Hook        | Command                                        | Effect                           |
| ----------- | ---------------------------------------------- | -------------------------------- |
| ruff format | `cd ./backend && poetry run ruff format .`     | Rewrites Python files            |
| ruff        | `cd ./backend && poetry run ruff check src`    | Reports issues; does not `--fix` |
| pytest      | `cd ./backend && poetry run pytest -m unit -v` | Unit tests only                  |

Pytest is `always_run: true` and `pass_filenames: false`: the whole unit suite runs, not only files in the commit.

## What does not run

- `mypy src` — GitHub Actions job `checks` runs it; the hook does not
- HTTP / integration tests, coverage, or Docker
- Commit-message linting — there is no `commit-msg` hook

Details: [Testing Guide](testing-guide.md).

## Install (once)

From `backend/`, with Poetry 1.8+ or 2.x:

```bash
cd backend
poetry install
poetry run pre-commit install
```

`pre-commit` is a Poetry dependency. The config file lives at the **git root**; `poetry run pre-commit install` from `backend/` still finds it.

After that, a normal `git commit` is enough. You do not need to activate the virtualenv for every commit if the hook was installed with that environment.

If you want the `pre-commit` CLI on your PATH, activate the venv:

```powershell
backend\.venv\Scripts\Activate.ps1
```

```bash
source backend/.venv/bin/activate
```

## Requirements

- **Poetry** on `PATH` — hook `entry` lines use `poetry run`
- **Git Bash** on Windows — hooks wrap commands in `bash -c '...'` (comes with [Git for Windows](https://git-scm.com/download/win))

## Run manually

From `backend/`:

```bash
cd backend
poetry run pre-commit run --all-files
```

Same three hooks as a commit, against the whole tree.

From the repo root, **Project Tools** (`python setup.py tools`) can run Ruff, mypy, and pytest without going through pre-commit.

## When a hook fails

1. **ruff format** rewrote files — `git add` the formatted files and commit again.
2. **ruff check** or **pytest** failed — fix the reported issue, then commit again.
3. Do not make `git commit --no-verify` a habit. Use it only for a conscious WIP commit when you know the hooks would fail.

Unit tests must pass **without Docker** and without `--cov`. If pytest wants Testcontainers, the test is marked wrong (`integration` vs `unit`). See the [Testing Guide](testing-guide.md).

## vs CI

|                           | Pre-commit hook  | GitHub Actions `checks` | GitHub Actions `test`      |
| ------------------------- | ---------------- | ----------------------- | -------------------------- |
| Ruff format               | writes files     | `--check` only          | —                          |
| Ruff lint                 | `ruff check src` | same                    | —                          |
| mypy                      | no               | `mypy src`              | —                          |
| Unit tests                | yes              | yes                     | included in the full suite |
| HTTP tests + 80% coverage | no               | no                      | yes (needs Docker)         |

---

[Back to backend README](../backend/README.md)
