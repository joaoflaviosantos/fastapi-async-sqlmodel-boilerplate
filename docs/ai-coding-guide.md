# Coding agents

This repository ships a small harness so coding agents follow the same backend layout as the rest of the project.

The harness is **intentionally universal**. It uses one always-on contract ([AGENTS.md](../AGENTS.md)), one skill directory ([.agents/skills/](../.agents/skills/)), and shared templates ([.agents/examples/](../.agents/examples/)), instead of per-tool trees (`.cursor/`, `.claude/`, `.opencode/`). That is the [Agent Skills](https://agentskills.io/) layout plus a project `examples/` folder, so the same repo works in Cursor, OpenCode, Google Antigravity, Codex, Gemini CLI, Amp, and similar tools that read `AGENTS.md` and/or `.agents/skills/`.

Do not duplicate first-party skills or examples into `.cursor/skills/`, `.claude/skills/`, or `.opencode/skills/`. Do not add `.agents/workflows/` or `.agent/rules/` — those are tool-specific.

## What is already in the repo

| Path                                      | Role                                                                                                      |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| [AGENTS.md](../AGENTS.md)                 | Always-on conventions: apps/subapps, router → service → repository, registration checklist, commands.     |
| [.agents/skills/](../.agents/skills/)     | On-demand recipes (`create-subapp`, `sqlmodel`, `fastapi`, `celery`, `alembic`, `write-tests`, `locust`). |
| [.agents/examples/](../.agents/examples/) | CRUD copy-target (`subapp/`) and Locust TaskSet template. Not a running app.                              |

Do not add `crud.py`. Do not flatten the tree into `app/api/v1/endpoints/`. Copy [`.agents/examples/subapp/`](../.agents/examples/subapp/) for a new resource (including `tasks.py` when you need Celery). Copy `backend/src/apps/system/users/` only for users-like work (auth, hashing). Sample apps such as `blog` may be missing in a clone.

## Instruction filename

`AGENTS.md` at the repository root is the instruction file. Keep extra, tool-specific notes out of it.

This repo does **not** commit tool adapters (no `CLAUDE.md`, no `.cursor/rules` copies of the same contract). That is deliberate: the maintainer does not use Claude Code, and adapters would lock the harness to one product.

If your tool does not load `AGENTS.md`, create **locally** (do not commit unless your team agrees) whatever file that tool expects, with a single include line:

```markdown
@AGENTS.md
```

Example: Claude Code reads `CLAUDE.md` at the root, not `AGENTS.md`, and does not scan `.agents/skills/` on its own. If you use Claude Code, create `CLAUDE.md` yourself with that one line. Do not copy conventions into the adapter. After the include, the agent follows `AGENTS.md`, including the paths to `.agents/skills/<name>/SKILL.md` and `.agents/examples/`.

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

`experimental_install` restores only what the lockfile lists. First-party skills and `.agents/examples/` come back from git.

### Do not overwrite first-party folders

`create-subapp`, `sqlmodel`, `fastapi`, `celery`, `alembic`, `write-tests`, `locust`, and `.agents/examples/`

Do not run `npx skills remove` on those skill names.

### Do not replace this backend’s architecture

Generic FastAPI / SQLModel / Celery packs (`fastapi-templates`, `sqlmodel-expert`, `celery-expert`, and similar) teach a different layout. They are fine for unrelated topics (review, frontend, etc.), not as a substitute for the skills in this repo.

## Related guides

- [Development Guide](development-guide.md)
- [Testing Guide](testing-guide.md)
- [Database Migration Guide](database-migration-guide.md)
- [Celery Guide](celery-guide.md)
- [Locust Guide](locust-guide.md)
