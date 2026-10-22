---
name: finishing-a-development-branch
description: Use after work is verified and the user wants options for merge, PR, branch retention, or cleanup - guides completion by presenting structured options and handling chosen workflow.
---

# Finishing a Development Branch

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

## Overview

After implementation is verified, the user needs a clear, safe path to integrate or discard work. This skill re-validates quality, surfaces exactly four outcomes, executes the chosen workflow, and cleans up worktrees when appropriate.

## When to Use

- Verification has already been run and quality checks are complete (or the user is explicitly asking how to finish).
- The user wants to merge, open a PR, keep the branch, or throw work away.
- Work was done in a worktree and cleanup must be coordinated with git state.

## Core Principle

**Verify tests → Present options → Execute choice → Clean up.**  
No merge or deletion without a green test run and explicit user confirmation where required.

## Preconditions

- Test/verification suite has been run for the current change set (user may request re-run; see step 1).
- User is asking what to do next with the branch/worktree—not mid-implementation without that intent.

## The Process

### 1. Re-verify Tests

Run the project’s standard test suite from the branch/worktree that holds the work.

- **If tests fail:** Stop. Show failures. Do **not** present merge/PR/cleanup options as safe until the user addresses failures or explicitly overrides with full awareness.

### 2. Determine Base Branch

Use `git merge-base` / team convention (e.g. `main`, `develop`) to identify the integration target. Confirm with the user if multiple long-lived branches exist.

### 3. Present Options (Exactly Four)

1. **Merge back to base locally** — Integrate into the local base branch and continue from one checkout.
2. **Push and create Pull Request** — Publish branch and open a PR for review.
3. **Keep branch as-is** — No merge; no PR; retain branch and worktree for later.
4. **Discard this work** — Remove branch (and optionally worktree) after explicit confirmation.

### 4. Execute Choice

| Option | Actions |
|--------|---------|
| **1 — Merge locally** | Checkout base branch, `git pull` (if remote tracking), merge feature branch, **re-run tests**, then delete the feature branch if merge succeeded and user wants it gone. |
| **2 — PR** | `git push -u origin <branch>`; `gh pr create` (or equivalent) with **summary + test plan** in the body. |
| **3 — Keep** | Report: **“Keeping branch. Worktree preserved.”** No destructive git commands. |
| **4 — Discard** | **Confirm first:** require the user to type **`discard`** (or agreed token). Then checkout base, delete the feature branch (`git branch -d` / `-D` only after confirmation). |

### 5. Cleanup Worktree

- For options **1, 2, and 4:** If work lived in a `git worktree`, remove that worktree (`git worktree remove`) when the user is done and paths are safe to delete—after merge/push/discard per workflow.
- For option **3:** **Do not** remove the worktree unless the user asks.

## Quick Reference

| Option | Merge base | Push remote | Keep worktree | Cleanup feature branch |
|--------|------------|-------------|---------------|-------------------------|
| 1 Local merge | Yes | Optional after | Remove after merge if desired | Usually yes after success |
| 2 PR | Via PR | Yes | Often keep until merged | After PR merged (user/CI) |
| 3 Keep | No | Optional | Yes | No |
| 4 Discard | No | No | Remove worktree | Yes (after `discard` confirm) |

## Red Flags

**Never:**

- Proceed with failing tests as if merge/PR is safe.
- Merge without re-verifying tests on the integration result (for local merge).
- Delete branches or destructive discard without confirmation (option 4).
- Force-push without an explicit user request.

## Integration

- **Called by:** `subagent-driven-development` and `executing-plans` when work is complete and integration is the next step.
- **Pairs with:** `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md` for creating and retiring isolated trees consistently.
