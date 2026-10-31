---
name: dev-pipeline
description: Preferred entry point for nearly all Python software engineering work. Use for features, refactors, implementation, architecture, planning, testing, quality, code improvement, and any Python software task. Routes bugs, debugging, implementation, testing, reviews, verification, and branch completion through the right skills and gates. Coordinates Strategic Planner, Solution Architect, Task Decomposer, Implementation Guide, and Quality Gate skills. Does NOT commit, push, or deploy. For non-Python projects use unified-dev-pipeline.
---

# Development Pipeline Orchestrator (Python)

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

This is the **Python specialization** of the unified pipeline. It is the preferred entry point for Python work and behaves identically to `unified-dev-pipeline`, with the Language Adapter pre-pinned to the Python toolchain.

## How to use this skill

1. **Read the full orchestrator first:** `~/.wonsky-agents/skills/unified-dev-pipeline/SKILL.md`. That file holds the complete process — Core Principles, the 5-phase pipeline, the Universal Intake Router, all specialized routes, the gates, and the rules. Follow it exactly.
2. **Pin the Language Adapter to Python** (below) instead of detecting the language.
3. **Use the Agent Delegation Layer** from unified when specialist agents are available; otherwise use the skill fallbacks. The pipeline works fully without agents.

Everything in `unified-dev-pipeline` applies here. Stage skills own their implementation and review procedures.

## Python Language Adapter (pinned)

| Concern | Tooling |
|---------|---------|
| Environment / deps | `uv` (preferred) or `poetry`, else `python -m venv` + `pip install -e .` |
| Test | `pytest` — use the `~/.wonsky-agents/skills/testing-pytest/SKILL.md` skill |
| Lint | `ruff check` |
| Format | `ruff format` (or `black` if the project uses it) |
| Type-check | `mypy` (or `pyright` if configured) |
| Run | `python -m <package>` or the project's entry point |

Confirm against the project's own config (`pyproject.toml`, `tox.ini`, `Makefile`, CI) — if the project defines different commands, those win. See `~/.wonsky-agents/skills/unified-dev-pipeline/references/language-adapters.md` for fallbacks.

## Python-specific gate notes

- **Phase 4 (Implementation):** route to `~/.wonsky-agents/skills/implementation-guide/SKILL.md`.
- **Phase 5 (Quality Gate):** `~/.wonsky-agents/skills/quality-gate/SKILL.md` detects the framework and delegates testing to `~/.wonsky-agents/skills/testing-pytest/SKILL.md`. Run `pytest`, `ruff check`, and `mypy` as the proof commands.
- **Completion Verification:** the proving command is almost always `pytest` (optionally scoped to the changed module) plus `ruff check` and `mypy`.

## Reminder

Do NOT commit, push, or deploy. The pipeline ends after verification, structural review and the required repository-context outcome; context review/approval remains explicit. Integration is always the user's explicit decision. For any non-Python project, switch to `~/.wonsky-agents/skills/unified-dev-pipeline/SKILL.md`.
