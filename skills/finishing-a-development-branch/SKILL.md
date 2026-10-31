---
name: finishing-a-development-branch
description: Use after work is verified and the user wants options for merge, PR, branch retention, or cleanup - guides completion by presenting structured options and handling chosen workflow.
---

# Finishing a Development Branch

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

## Overview

After implementation is verified, the user needs a clear, safe path to integrate or discard work. This skill checks delivery evidence and Git state, offers integration choices when needed, executes the authorized choice and cleans up only when safe.

## When to Use

- Verification has already been run and quality checks are complete (or the user is explicitly asking how to finish).
- The user wants to merge, open a PR, keep the branch, or throw work away.
- Work was done in a worktree and cleanup must be coordinated with git state.

## Core Principle

**Inspect Git state → Verify applicable evidence → Execute the authorized choice → Clean up safely.**
Commit, push, merge and discard require explicit user intent; existing authorization is reused. A clean test run does not prove uncommitted work is included in HEAD.

## Preconditions

- Test/verification suite has been run for the current change set (user may request re-run; see step 1).
- User is asking what to do next with the branch/worktree—not mid-implementation without that intent.

## The Process

### 1. Inspect Git state and verification

Inventory the current branch/HEAD, intended base, staged changes, unstaged changes and relevant untracked files. Separate the requested delivery from pre-existing work. Inspect the exact diff that would be committed or integrated; `git push` and a PR include committed history only.

If intended implementation is uncommitted, present its concrete commit scope and obtain commit intent before committing. Do not stage unrelated files, stash, reset, switch branches with dirty work or claim a PR includes those changes. A user may explicitly choose to publish only existing commits; state the omitted local work.

Use `verification-before-completion` to assess evidence for the exact delivered revision. Reuse valid evidence when inputs are unchanged. Run tests only when requested and permitted; report unverified scope honestly. If tests fail, do not describe integration as safe without a fully informed user override.

### 2. Determine Base Branch

Use `git merge-base` / team convention (e.g. `main`, `develop`) to identify the integration target. Confirm with the user if multiple long-lived branches exist.

### 3. Use the chosen option, or offer these four when undecided

1. **Merge back to base locally** — Integrate into the local base branch and continue from one checkout.
2. **Push and create Pull Request** — Publish branch and open a PR for review.
3. **Keep branch as-is** — No merge; no PR; retain branch and worktree for later.
4. **Discard this work** — Remove branch (and optionally worktree) after explicit confirmation.

### 4. Execute Choice

| Option | Actions |
|--------|---------|
| **1 — Merge locally** | Require clean source and destination checkouts and the intended work in committed history. Use the confirmed base; refresh remote state if authorized. Merge, verify the integration result with applicable authorized checks, and delete the feature branch only if requested. |
| **2 — PR** | Confirm the exact committed range and destination, then push and create the PR with summary and actual verification evidence/limits. Attach the created PR in hosts that provide artifact attachment. Keep local changes explicitly accounted for. |
| **3 — Keep** | Report: **“Keeping branch. Worktree preserved.”** No destructive git commands. |
| **4 — Discard** | **Confirm first:** require the user to type **`discard`** (or agreed token). Then checkout base, delete the feature branch (`git branch -d` / `-D` only after confirmation). |

### 5. Cleanup Worktree

- Remove a worktree only when the user intends cleanup, it contains no needed local work and the relevant merge/discard is complete. Opening a PR alone is not a reason to remove its worktree. Recheck staged/unstaged/untracked and ignored files before any removal; use the host's managed archive tool when available.
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
- Claim the integration result verified using evidence from a different revision or environment.
- Delete branches or destructive discard without confirmation (option 4).
- Force-push without an explicit user request.

## Integration

- **Called by:** `subagent-driven-development` and `executing-plans` when work is complete and integration is the next step.
- **Pairs with:** `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md` for creating and retiring isolated trees consistently.
