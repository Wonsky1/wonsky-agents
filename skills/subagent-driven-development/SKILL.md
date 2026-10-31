---
name: subagent-driven-development
description: Use when an approved implementation plan exists and tasks can be executed task-by-task with delegated implementation and review - dispatches fresh subagent per task with code review between tasks for fast iteration with quality gates.
---

# Subagent-Driven Development

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

Execute an approved plan with scoped implementation and both spec-compliance and code-quality review. Use fresh task/batch agents when delegation provides useful isolation; a small cohesive low-risk batch may use one independent reviewer covering both lenses. Keep separate reviews for substantial or sensitive changes.

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

For each delegated task or small cohesive batch, provide:

- Exact task text (paste full task)
- Architecture / file-ownership context
- Verification expectations
- Instruction: implement exactly the task; use tests/TDD when test work is requested and permitted; self-review and report verification evidence/limits

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

- Inspect the actual diff and complete verification output; check that inputs/environment match the integrated result. Do not trust a success summary alone. Reuse valid unchanged evidence; rerun authorized checks when relevant inputs changed or evidence is incomplete.
- Only then mark the task verified, or explicitly report its unverified limits

### 6. Finish Plan

After **all** tasks:

- Request a **final** code review if warranted (`~/.wonsky-agents/skills/requesting-code-review/SKILL.md`)
- Run `~/.wonsky-agents/skills/quality-gate/SKILL.md`
- Run `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`
- Close the required repository-context outcome (updated, verified-current with evidence, draft-awaiting-review, exact policy proposal pending-approval, or user-declined). Missing factual coverage requires actual reviewable drafts under repository-context; a plan/test report is not repository context. Ask the user to review those drafts and report pending review separately.
- Use `~/.wonsky-agents/skills/finishing-a-development-branch/SKILL.md` when the user requests integration/cleanup; no implicit commit or push

## Rules

- **No parallel implementers** on overlapping scopes (same files or conflicting edits)
- **Do not skip** spec review or code quality review
- **Do not trust** “done” without inspecting the work and current supporting evidence
- **Scale delegation to the task**; batch related low-risk steps when this avoids duplicated setup without hiding responsibilities or skipping either review lens
- If a task keeps bouncing between implementer and reviewers, **reassess the plan** rather than retrying blindly

## Related Skills

- `~/.wonsky-agents/skills/test-driven-development/SKILL.md` — behavior changes
- `~/.wonsky-agents/skills/implementation-guide/SKILL.md` — structure and SOLID
- `~/.wonsky-agents/skills/dispatching-parallel-agents/SKILL.md` — parallel **investigations**, not conflicting implementations

## Context handoff

Pass the repository-context packet with every plan or delegated task: repo root, outcome, read/write boundaries, applicable instructions, selected documents and freshness evidence, unresolved conflicts, and exact protected-document approvals. Each fresh worker reads the applicable guidance; a summary is not a replacement. Recheck changed documents on resume and instruction chains for new targets. Do not inherit broader permissions from another worker.
