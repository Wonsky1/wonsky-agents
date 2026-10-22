# Spec Reviewer Prompt Template

Use this template to verify implementation matches the task specification.

```text
Read `~/.wonsky-agents/skills/repository-context/SKILL.md` before repository work.
Repository context packet: [root, task, read/write boundaries, applicable instruction/document paths, freshness evidence, unresolved conflicts, exact approved protected-document changes and authorizing user message]. Read the applicable guidance; do not infer write approval from an implementer summary or plan. Report context changes and pending proposals in your handoff.

Review this implementation against the task specification.

## Task Specification
[FULL task text]

## What Was Implemented
[Summary from implementer]

## Check

1. Does the implementation satisfy every requirement in the task?
2. Is anything missing from the spec?
3. Was anything added that the spec did not ask for?
4. Are verification criteria met?

## Output

- Requirements met: [list]
- Requirements missed: [list]
- Extra scope added: [list]
- Verdict: PASS | NEEDS_WORK
- Details: [specifics for any missed or extra items]
```
