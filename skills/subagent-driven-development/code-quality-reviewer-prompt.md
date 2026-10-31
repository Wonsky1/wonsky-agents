# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality review after spec compliance passes.

```text
Read `~/.wonsky-agents/skills/repository-context/SKILL.md` before repository work.
Repository context packet: [root, task, read/write boundaries, applicable instruction/document paths, freshness evidence, unresolved conflicts, exact approved protected-document changes and authorizing user message]. Read the applicable guidance; do not infer write approval from an implementer summary or plan. Report factual drafts, user review status and exact policy approvals in your handoff.

Review this implementation for:
- bugs
- maintainability
- edge cases
- test gaps
- alignment with planned structure and, for Python, the required implementation-guide/references/python-structure.md contract (read it first); inspect its required evidence in the actual changes
- required repository-context outcome with actual paths/evidence; report pending context review or policy approval explicitly

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
