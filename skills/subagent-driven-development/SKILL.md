---
name: subagent-driven-development
description: Use when an approved implementation plan exists and tasks can be executed task-by-task with delegated implementation and review - dispatches fresh subagent per task with code review between tasks for fast iteration with quality gates.
---

# Subagent-Driven Development

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

Execute an approved plan by dispatching a **fresh subagent per task**, with **spec compliance** and **code quality** review between tasks.

**Core principle:** Fresh context per task + structured reviews = fast iteration without sacrificing quality.

## When to Use vs Alternatives

| Situation | Prefer |
|-----------|--------|
| Same session, tasks mostly independent, want continuous progress with gates | **This skill** (`subagent-driven-development`) |
| Human-in-the-loop between **batches** of tasks, sequential execution in one thread | `~/.wonsky-agents/skills/executing-plans/SKILL.md` |
| Tightly coupled tasks, heavy shared context, or plan still in flux | Manual execution; revise plan (`~/.wonsky-agents/skills/writing-plans/SKILL.md` / brainstorming) first |

**When NOT to use this skill:**

- Plan needs revision or scope is unclear — clarify first
- Tasks require one shared mental model with no clean handoff boundaries
- You would need **parallel implementers** on **overlapping** files — use sequential implementers instead

## Workflow

### 1. Load Plan

- Read the plan once; extract ordered tasks and dependencies
- Create **TodoWrite** (or equivalent) for all tasks
- Set up an isolated workspace / branch if appropriate (`~/.wonsky-agents/skills/using-git-worktrees/SKILL.md` when relevant)

### 2. Dispatch Implementer

For **each** task, dispatch one implementation subagent with:

- Exact task text (paste full task)
- Architecture / file-ownership context
- Verification expectations
- Instruction: implement exactly the task; use tests/TDD when behavior changes; self-verify before reporting

**Do not** make the implementer rediscover the entire plan.

Use the prompt structure in:

`~/.wonsky-agents/skills/subagent-driven-development/implementer-prompt.md`

### 3. Run Spec Review

After implementation, verify **requirements match the task** (not just “it runs”):

`~/.wonsky-agents/skills/subagent-driven-development/spec-reviewer-prompt.md`

If requirements are missed or extra scope appeared, send back for correction before quality review.

### 4. Run Code Quality Review

After spec compliance passes, review for bugs, maintainability, edge cases, test gaps, and alignment with the planned structure:

`~/.wonsky-agents/skills/subagent-driven-development/code-quality-reviewer-prompt.md`

### 5. Verify and Close Task

- Run the task’s verification **yourself** (do not trust the subagent report alone)
- Only then mark the task completed and move to the next

### 6. Finish Plan

After **all** tasks:

- Request a **final** code review if warranted (`~/.wonsky-agents/skills/requesting-code-review/SKILL.md`)
- Run `~/.wonsky-agents/skills/quality-gate/SKILL.md`
- Run `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`
- Use `~/.wonsky-agents/skills/finishing-a-development-branch/SKILL.md` for merge/PR/cleanup options

## Rules

- **No parallel implementers** on overlapping scopes (same files or conflicting edits)
- **Do not skip** spec review or code quality review
- **Do not trust** “done” without running verification locally
- **Prefer one implementer per task**, not one subagent for the whole plan
- If a task keeps bouncing between implementer and reviewers, **reassess the plan** rather than retrying blindly

## Related Skills

- `~/.wonsky-agents/skills/test-driven-development/SKILL.md` — behavior changes
- `~/.wonsky-agents/skills/implementation-guide/SKILL.md` — structure and SOLID
- `~/.wonsky-agents/skills/dispatching-parallel-agents/SKILL.md` — parallel **investigations**, not conflicting implementations

## Context handoff

Pass the repository-context packet with every plan or delegated task: repo root, outcome, read/write boundaries, applicable instructions, selected documents and freshness evidence, unresolved conflicts, and exact protected-document approvals. Each fresh worker reads the applicable guidance; a summary is not a replacement. Recheck changed documents on resume and instruction chains for new targets. Do not inherit broader permissions from another worker.
