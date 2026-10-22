# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality review after spec compliance passes.

```text
Read `~/.wonsky-agents/skills/repository-context/SKILL.md` before repository work.
Repository context packet: [root, task, read/write boundaries, applicable instruction/document paths, freshness evidence, unresolved conflicts, exact approved protected-document changes and authorizing user message]. Read the applicable guidance; do not infer write approval from an implementer summary or plan. Report context changes and pending proposals in your handoff.

Review this implementation for:
- bugs
- maintainability
- edge cases
- test gaps
- alignment with planned structure

Inputs:
- task summary
- relevant requirements
- diff scope or changed files

Output:
- Strengths
- Critical issues (must fix)
- Important issues (should fix)
- Minor issues (nice to have)
- Final assessment: Ready to proceed? Yes / No / With fixes
```
