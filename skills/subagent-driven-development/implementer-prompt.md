# Implementer Subagent Prompt Template

Use this template when dispatching an implementation subagent.

```text
Read `~/.wonsky-agents/skills/repository-context/SKILL.md` before repository work.
Repository context packet: [root, task, read/write boundaries, applicable instruction/document paths, freshness evidence, unresolved conflicts, exact approved protected-document changes and authorizing user message]. Read the applicable guidance; do not infer write approval from an implementer summary or plan. Report factual drafts, user review status and exact policy approvals in your handoff.

You are implementing Task N: [task name]

## Task Description
[FULL task text pasted here]

## Context
[Architecture, dependencies, and why this task exists]

## Before You Begin

If anything is unclear about requirements, approach, dependencies, or assumptions, ask now.
Do not guess.

## Your Job

1. Read implementation-guide/SKILL.md and, for Python, its references/python-structure.md from the canonical skill directory. Apply that contract even if the task omitted it; surface required scope/API migrations before breaking callers. Implement the authorized task.
2. Read test-driven-development/references/behavioral-verification.md from the supplied skill root. Carry the requested mode and explicit limits; add useful missing behavior/regression coverage with TDD, not tests that freeze internals.
3. Verify the actual functionality, meaningful edge cases and relevant real boundaries; map acceptance criteria to checks/results or limitations
4. Self-review before reporting back

## Report Format

- Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What changed
- What was verified
- Files changed
- Model and dependency owner files (or why absent); structure-check result and semantic review
- Required context outcome with paths/evidence; exact proposals and approval state
- Concerns or blockers
```
