---
name: writing-plans
description: Use when design is complete and you need detailed implementation tasks for engineers with zero codebase context - creates comprehensive implementation plans with exact file paths, complete code examples, and verification steps assuming engineer has minimal domain knowledge.
---

# Writing Plans

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

## Overview

Produce an implementation plan as **bite-sized tasks** for someone who is a **strong developer** but has **almost no context** for this repository or domain. Document files to touch, code and tests, commands, and expected outcomes. Prefer **DRY**, **YAGNI**, **TDD**, and **small frequent commits**.

**Announce at the start:** you are using the writing-plans skill to build the plan.

**Default save location:**

`docs/plans/YYYY-MM-DD-<feature-name>.md`

Override if the user or project standardizes a different path.

## Scope check

If the design still bundles **multiple independent subsystems**, stop: split into separate plans (one cohesive, shippable increment per plan). Each plan should result in working, testable software on its own.

## File structure (plan the tree before tasks)

Before tasks, map **create / modify** files and each file’s single responsibility.

- Clear boundaries and interfaces; one main responsibility per file.
- Prefer focused files over kitchen-sink modules.
- **Co-location:** things that change together should live together; split by responsibility, not by ceremonial layers.
- In existing repos, **follow established patterns**. If a file you touch is unwieldy, the plan may include a justified split — not a drive-by restructure.

## Task granularity

Treat each atomic step as **~2–5 minutes** of work, for example:

1. Write the failing test  
2. Run it — confirm it fails for the right reason  
3. Implement the minimum to pass  
4. Run tests — confirm green  
5. Commit  

## Plan document header

**Every plan must begin with:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Implement this plan task-by-task. Use checkbox (`- [ ]`) steps for tracking. Preferred execution skills: `~/.wonsky-agents/skills/subagent-driven-development/SKILL.md` (this session, per-task subagents) or a parallel session with `~/.wonsky-agents/skills/executing-plans/SKILL.md`.

**Goal:** [One sentence: what this delivers]

**Architecture:** [2–3 sentences on approach and boundaries]

**Tech Stack:** [Languages, frameworks, key libraries, test runner]

---
```

## Task template

Use this shape for every task. Adjust language to the project (Python, TS, Go, etc.).

````markdown
### Task N: [Component or behavior]

**Files:**
- Create: `exact/path/to/new/file.ext`
- Modify: `exact/path/to/existing.ext` (note function or region if helpful)
- Test: `exact/path/to/test_file.ext`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function_under_test(input)
    assert result == expected
```

- [ ] **Step 2: Run test — expect failure**

Run: `pytest tests/path/test_file.py::test_specific_behavior -v`  
Expected: **FAIL** (e.g. missing symbol or wrong behavior)

- [ ] **Step 3: Minimal implementation**

```python
def function_under_test(input):
    return expected
```

- [ ] **Step 4: Run test — expect pass**

Run: `pytest tests/path/test_file.py::test_specific_behavior -v`  
Expected: **PASS**

- [ ] **Step 5: Commit**

```bash
git add tests/path/test_file.py src/path/file.py
git commit -m "feat: describe the behavior"
```
````

## Quality bar for the document

- **Exact file paths** — no vague “the handler file.”
- **Complete code** in the plan — not “add validation here.”
- **Exact commands** with **expected output** (pass/fail messages, key log lines).
- **Cross-references** to other skills use only: `~/.wonsky-agents/skills/{skill-name}/SKILL.md`.

## Optional review

If the team uses plan review, run it **after** the full plan exists, with a fresh prompt focused on the plan + design doc paths — not raw chat history. If review loops exceed a few iterations, escalate to the human.

## Execution handoff

After saving the plan, offer:

---

**Plan saved to** `docs/plans/YYYY-MM-DD-<feature-name>.md`. **Choose execution:**

1. **Subagent-driven (this session)** — fresh subagent per task (or per small batch), review between steps. Use `~/.wonsky-agents/skills/subagent-driven-development/SKILL.md`.

2. **Parallel session** — run the plan in another chat or worktree with checkpointed batches. Use `~/.wonsky-agents/skills/executing-plans/SKILL.md`.

Which approach do you want?

---

## Related skills

| Need | Skill |
|------|--------|
| Design before planning | `~/.wonsky-agents/skills/brainstorming/SKILL.md` |
| Program-level scope and risks | `~/.wonsky-agents/skills/strategic-planner/SKILL.md` |
| Isolated branch / worktree | `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md` |

## Context handoff

Pass the repository-context packet with every plan or delegated task: repo root, outcome, read/write boundaries, applicable instructions, selected documents and freshness evidence, unresolved conflicts, and exact protected-document approvals. Each fresh worker reads the applicable guidance; a summary is not a replacement. Recheck changed documents on resume and instruction chains for new targets. Do not inherit broader permissions from another worker.
