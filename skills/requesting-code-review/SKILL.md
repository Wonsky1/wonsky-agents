---
name: requesting-code-review
description: Use after completing a major task, batch of implementation work, complex bug fix, or before merge to verify work meets requirements - dispatches reviewer subagent to review implementation against plan or requirements.
---

# Requesting Code Review

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

Catch requirement gaps, regressions, and quality issues **before** they compound. Prefer an independent pass over self-review alone.

**Related:** If review feedback looks wrong or you are unsure how to apply it, read `~/.wonsky-agents/skills/receiving-code-review/SKILL.md` before changing code.

For Python review, read `~/.wonsky-agents/skills/implementation-guide/references/python-structure.md` and pass it with every delegated review task. Review its required evidence rather than duplicating its rules here.

## When to Use

### Mandatory

- **After each meaningful task or cohesive low-risk batch** in `~/.wonsky-agents/skills/subagent-driven-development/SKILL.md`; review both requirements and quality. One independent combined pass may cover a small batch.
- **After a major feature** or substantial batch of implementation work tied to a plan.
- **Before merge** (or before opening a PR if that is your integration point).

### Optional but valuable

- When **stuck** or uncertain whether the approach matches requirements — a reviewer can spot blind spots.
- **Before refactoring** a sensitive area — establish a baseline review of current behavior and risk.
- **After a complex bug fix** — confirm the fix does not trade one failure mode for another.

## Review Package

Before requesting review, assemble a concise package:

| Element | Include |
|--------|---------|
| **What was implemented** | Summary of behavior and scope, not just file names. |
| **Requirements / plan reference** | Link, excerpt, or pasted acceptance criteria the work must satisfy. |
| **Changed files / diff scope** | Paths, rough size, or areas (e.g. “auth + API layer”). |
| **Verification already run** | Tests, linters, manual checks — what passed and what was skipped (with reason). |
| **Known concerns** | Tradeoffs, TODOs, areas you already doubt — invites focused review. |

## Review Methods

### Preferred: Independent Reviewer (subagent)

When subagents or a separate reviewer context is available:

1. Give the reviewer **only** the work product, requirements and repository-context packet — **not** your full conversation history (reduces anchoring and confirmation bias).
2. Keep the reviewer focused on: bugs, regressions, requirement mismatches, test gaps, security/performance red flags, and meaningful maintainability regressions.
3. Use the template at `~/.wonsky-agents/skills/requesting-code-review/code-reviewer.md` as the body of the review request; fill every placeholder.

**Why subagent:** A fresh reader simulates how another engineer (or production) will encounter the change.

### Fallback: Structured Local Review

If no reviewer agent is available:

1. Open the plan or requirements **side by side** with the diff.
2. Walk the diff **line by line** against the plan: each requirement → evidence in code.
3. Explicitly look for: missing requirements, **extra** unrequested scope, risky edge cases, missing or weak tests.
4. For a stricter maintainability pass, read `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md` and apply it before low-level polish feedback.

## How to Request

1. **Identify the actual review input**
   - Choose committed range, working tree (including staged/untracked work), or an explicit supplied diff for non-Git work. State exact paths and separate pre-existing changes.
   - For committed work, record verified base/head SHAs. For local work, do not use a SHA-only diff that omits the implementation.
2. **Fill `code-reviewer.md`**
   - `{DESCRIPTION}`, `{PLAN_REFERENCE}`, `{REVIEW_MODE}`, `{REVIEW_PATHS}`, `{REVIEW_EVIDENCE}`, `{REPOSITORY_CONTEXT_PACKET}`, and align `{WHAT_WAS_IMPLEMENTED}` / `{PLAN_OR_REQUIREMENTS}` with your package.
3. **Dispatch the reviewer**
   - Paste the completed template (or attach the file path) including the complete repository-context packet and the scoped review evidence. Keep irrelevant conversation history out of the payload.
4. **Incorporate findings** using the severity ladder below; if a finding does not hold up on inspection, switch to `~/.wonsky-agents/skills/receiving-code-review/SKILL.md`.

## Handling Findings

| Severity | Action |
|----------|--------|
| **Critical** | Fix **immediately** — broken behavior, security, data loss, severe regressions. |
| **Important** | Fix **before** proceeding — missing requirements, risky edge cases, significant test gaps. |
| **Minor** | **Record**; address if worthwhile — polish, naming, non-blocking cleanup. |

**If feedback seems wrong, incomplete, or contradictory:** do **not** implement blindly — route through `~/.wonsky-agents/skills/receiving-code-review/SKILL.md` (verify, then fix or push back with reasoning).

## Red Flags (avoid these)

- **Skipping both review lenses** because a change seems small; scale the review rather than omitting it.
- **Reviewing without requirements** in hand — you cannot assess completeness.
- **Ignoring Important findings** to save time.
- **Treating “tests pass” as “requirements met”** — tests can be wrong or incomplete; align to the plan.
- **Biasing the reviewer** with a long narrative instead of facts + template — keep the review package tight.

## Context handoff

Pass the repository-context packet with every plan or delegated task: repo root, outcome, read/write boundaries, applicable instructions, selected documents and freshness evidence, unresolved conflicts, and exact protected-document approvals. Each fresh worker reads the applicable guidance; a summary is not a replacement. Recheck changed documents on resume and instruction chains for new targets. Do not inherit broader permissions from another worker.
