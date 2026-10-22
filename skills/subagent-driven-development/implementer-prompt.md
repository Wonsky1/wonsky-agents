# Implementer Subagent Prompt Template

Use this template when dispatching an implementation subagent.

```text
Read `~/.wonsky-agents/skills/repository-context/SKILL.md` before repository work.
Repository context packet: [root, task, read/write boundaries, applicable instruction/document paths, freshness evidence, unresolved conflicts, exact approved protected-document changes and authorizing user message]. Read the applicable guidance; do not infer write approval from an implementer summary or plan. Report context changes and pending proposals in your handoff.

You are implementing Task N: [task name]

## Task Description
[FULL task text pasted here]

## Context
[Architecture, dependencies, and why this task exists]

## Before You Begin

If anything is unclear about requirements, approach, dependencies, or assumptions, ask now.
Do not guess.

## Your Job

1. Implement exactly what the task specifies
2. Use tests / TDD when the task changes behavior
3. Verify the implementation
4. Self-review before reporting back

## Report Format

- Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What changed
- What was verified
- Files changed
- Concerns or blockers
```
