---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification.
---

# Using Git Worktrees

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

## Overview

Isolated feature work reduces merge pain and keeps the main workspace clean. This skill standardizes how to pick a worktree location, verify safety, bootstrap the clone, and confirm a clean baseline.

## When to Use

- Starting feature work that should not touch the current checkout.
- Before executing an implementation plan that needs a dedicated tree.
- When the user asks for parallel or isolated development without switching branches in place.

## Core Principle

**Systematic directory selection + safety verification = reliable isolation.**  
Never assume a path; never skip `.gitignore` for project-local trees; never treat an unverified tree as ready.

## Directory Selection Process

Apply in **priority order**:

1. **Check existing directories** — Look for `.worktrees/` or `worktrees/` already present and in use for this repo.
2. **Check project docs/config** — README, CONTRIBUTING, team conventions, or repo-specific rules that name a worktree location.
3. **Ask the user** — Offer clear options:
   - **Project-local (hidden):** `.worktrees/` (or agreed name) next to the repo.
   - **Global location:** e.g. `~/worktrees/<project>-<branch>/` or another team standard.

## Safety Verification

| Location        | `.gitignore` rule |
|----------------|-------------------|
| **Project-local** | **MUST** verify the worktree parent (e.g. `.worktrees/`) is listed in `.gitignore` **before** creating the directory. If missing, add it immediately and commit (or include in the same change set the user approves). |
| **Global**       | Not required for `.gitignore`; the tree lives outside the repo. |

## Creation Steps

1. **Detect project name** — From remote URL, directory name, or `package.json` / `Cargo.toml` metadata when helpful.
2. **Create worktree** — `git worktree add <path> -b <new-branch>` (or add existing branch per user intent).
3. **Run project setup** (auto-detect; run what applies):
   - `package.json` → `npm install` (or `pnpm install` / `yarn` if lockfiles indicate).
   - `Cargo.toml` → `cargo build`.
   - `requirements.txt` → `pip install -r requirements.txt`.
   - `pyproject.toml` → `poetry install` or `uv sync` per tool signals.
   - `go.mod` → `go mod download`.
4. **Verify clean baseline** — Run the project’s standard test command; report failures or confirm ready.
5. **Report location** — Give absolute path, branch name, and how to open the tree in Cursor.

## Quick Reference

| Step              | Action |
|-------------------|--------|
| Pick location     | Existing dirs → docs → ask user |
| Project-local     | `.gitignore` check **first** |
| Create            | `git worktree add` + new branch |
| Setup             | Detect manifest → install/build |
| Baseline          | Tests → pass or surface failures |
| Handoff           | Path + branch + next step |

## Common Mistakes

- Skipping `.gitignore` for project-local worktrees (pollutes `git status`).
- Assuming a location without checking docs or asking.
- Proceeding as if the tree is “ready” when tests fail.
- Hardcoding one setup command for all repos (ignore lockfiles and conventions).

## Red Flags

**Never:**

- Create a project-local worktree path without verifying `.gitignore`.
- Skip baseline verification after setup.
- Proceed with failing tests **without** telling the user and getting explicit direction.

## Integration

- **Called by:** `brainstorming` and any skill that requires an isolated tree before implementation.
- **Pairs with:** `~/.wonsky-agents/skills/finishing-a-development-branch/SKILL.md` for merge, PR, and cleanup after work is done.
