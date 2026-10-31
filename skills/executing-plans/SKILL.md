---
name: executing-plans
description: Use when you have an approved implementation plan to execute sequentially with checkpoints - loads plan, reviews critically, executes tasks in batches, reports for review between batches.
---

# Executing Plans

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

Execute an approved plan faithfully in **controlled batches** with verification and human review between batches.

**Core principle:** Batch execution with visible checkpoints. Reuse explicit end-to-end execution authorization; pause for decisions, requested checkpoints or blockers rather than requiring another confirmation after every routine batch.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## Before You Start

1. Read the full plan.
2. Review it critically before touching code.
3. If the plan has major gaps, stop and send it back to planning / decomposition.
4. If subagents are available and tasks are mostly independent, consider `~/.wonsky-agents/skills/subagent-driven-development/SKILL.md` for same-session delegation with reviews.

## The Process

### Step 1: Load and Review Plan

1. Read the plan file end-to-end.
2. Review critically — identify questions, risks, or unclear steps.
3. If concerns: raise them with the user **before** starting (or capture them in TodoWrite as blockers).
4. If no blocking concerns: create **TodoWrite** (or equivalent task list) aligned with the plan and proceed.

### Step 2: Execute Batch

**Default: first 3 tasks** in plan order (adjust if the plan defines a different batch size).

For each task in the batch:

1. Mark as **in_progress**
2. Follow each step **exactly** as written (plans should be bite-sized)
3. Perform authorized verification and retain evidence for the exact inputs; do not add/run tests unless requested and permitted
4. Mark as **completed** only after verification passes

Use `~/.wonsky-agents/skills/implementation-guide/SKILL.md` while coding. For behavior changes, follow `~/.wonsky-agents/skills/test-driven-development/SKILL.md`.

### Step 3: Report

When the batch is complete:

- Summarize what was implemented (files, behavior)
- Show **verification output** (commands run and key results)
- Say: **"Ready for feedback."**

If the user authorized the whole plan, continue independent in-scope batches after the update. Wait when the plan/user requires approval, an unresolved decision affects correctness or the next action is outside existing authority. Follow repository-context for factual drafts and exact policy approvals.

### Step 4: Continue

Based on feedback:

- Apply requested changes
- Execute the **next** batch of tasks
- Repeat Steps 2–4 until all tasks are done

**Return to Step 1 (re-review)** when the user updates the plan materially or the approach needs rethinking.

### Step 5: Complete Development

After all tasks are complete and verified:

- Run `~/.wonsky-agents/skills/quality-gate/SKILL.md`
- Run `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`
- Close the required repository-context outcome (updated, verified-current with evidence, draft-awaiting-review, exact policy proposal pending-approval, or user-declined). Missing factual coverage requires actual reviewable drafts under repository-context; a plan/test report is not repository context. Ask the user to review those drafts and report pending review separately.
- Use `~/.wonsky-agents/skills/finishing-a-development-branch/SKILL.md` only when integration/cleanup is requested; otherwise report the delivered working-tree changes and evidence without committing or pushing

## When to Stop and Ask for Help

**Stop executing immediately when:**

- You hit a blocker mid-batch (missing dependency, repeated test failure, ambiguous instruction)
- The plan has critical gaps that prevent safe execution
- You don’t understand an instruction
- Verification fails repeatedly after a reasonable fix attempt

**Ask for clarification rather than guessing.**

## Stop Conditions

Pause and escalate (user or plan owner) when:

| Condition | Why it matters |
|-----------|----------------|
| **Ambiguous plan** | Wrong implementation is worse than waiting |
| **Wrong architecture** | Executing a bad design compounds cost |
| **Repeated verification failure** | Signals misunderstanding or environment issue |
| **Hidden dependencies** | Task order or scope may be invalid; brute force wastes time |

## Anti-patterns

- Implementing from memory instead of from the plan
- Skipping verification because “a later task will touch the same code”
- Silently changing plan scope
- Forcing through blockers instead of stopping

## Remember

- Review the plan critically first
- Follow plan steps exactly
- Don’t skip verifications
- Reference other skills when the plan says to
- Between batches: report; wait only at required approvals or blockers
- Stop when blocked; don’t guess

## Context handoff

Pass the repository-context packet with every plan or delegated task: repo root, outcome, read/write boundaries, applicable instructions, selected documents and freshness evidence, unresolved conflicts, and exact protected-document approvals. Each fresh worker reads the applicable guidance; a summary is not a replacement. Recheck changed documents on resume and instruction chains for new targets. Do not inherit broader permissions from another worker.
