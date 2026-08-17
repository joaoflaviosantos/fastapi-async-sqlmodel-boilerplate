# Coding agents

This repository ships a small harness so coding agents follow the same backend layout as the rest of the project.

## What is already in the repo

| Path                                  | Role                                                                                                      |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| [AGENTS.md](../AGENTS.md)             | Always-on conventions: apps/subapps, router → service → repository, registration checklist, commands.     |
| [.agents/skills/](../.agents/skills/) | On-demand recipes (`create-subapp`, `sqlmodel`, `fastapi`, `celery`, `alembic`, `write-tests`, `locust`). |

Do not add `crud.py`. Do not flatten the tree into `app/api/v1/endpoints/`. Copy `backend/src/apps/blog/posts/` or `backend/src/apps/system/users/`.

## Instruction filename

`AGENTS.md` at the repository root is the instruction file. If a tool does not load that name, add whatever instruction file it expects at the root, with a single include line:

```markdown
@AGENTS.md
```

Claude Code loads `CLAUDE.md` at the root, not `AGENTS.md`. Create `CLAUDE.md` there with that one line. Do not copy conventions into `CLAUDE.md`; keep extra, tool-specific notes only in that adapter file.

Keep extra, tool-specific notes out of `AGENTS.md`.

## Extra skills

First-party skills above are git-tracked. They are **not** listed in a lockfile.

To install additional packs from [skills.sh](https://skills.sh/):

```bash
npx skills add owner/repo --skill skill-name
npx skills check
npx skills update
npx skills experimental_install
```

The first `npx skills add` creates `skills-lock.json` at the repository root (source + content hash per pack). Later adds merge into the same file. Commit `skills-lock.json` together with any new folders under `.agents/skills/`.

`experimental_install` restores only what the lockfile lists. First-party skills come back from git.

### Do not overwrite first-party folders

`create-subapp`, `sqlmodel`, `fastapi`, `celery`, `alembic`, `write-tests`, `locust`

Do not run `npx skills remove` on those names.

### Do not replace this backend’s architecture

Generic FastAPI / SQLModel / Celery packs (`fastapi-templates`, `sqlmodel-expert`, `celery-expert`, and similar) teach a different layout. They are fine for unrelated topics (review, frontend, etc.), not as a substitute for the skills in this repo.

## Related guides

- [Development Guide](development-guide.md)
- [Testing Guide](testing-guide.md)
- [Database Migration Guide](database-migration-guide.md)
- [Celery Guide](celery-guide.md)
- [Locust Guide](locust-guide.md)
