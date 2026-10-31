---
name: receiving-code-review
description: Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation.
---

# Receiving Code Review

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

**Skill type:** discipline — this governs *how* you respond to feedback, not whether you are “nice.”

**Related:** To request a structured review in the first place, use `~/.wonsky-agents/skills/requesting-code-review/SKILL.md`.

## Core Principle

**Verify before implementing. Ask before assuming. Technical correctness over social comfort.**

Review comments — including from tools or external reviewers — are **hypotheses** until validated against the code, tests, and requirements. Your job is to **evaluate**, not to **obey**.

Rationalizations that feel reasonable in the moment (“they’re senior,” “it’s faster to just do it,” “I don’t want to seem difficult”) are **explicitly out of scope**. Only evidence in the codebase and specs counts.

## Response Pattern

Follow this order **every time**. Do not skip steps because feedback “sounds right.”

1. **READ** — Full feedback set, end to end. No partial reads.
2. **UNDERSTAND** — Restate each item in your own words as a concrete claim about code or behavior.
3. **VERIFY** — Open the code, run tests, trace call paths. Confirm or falsify each claim with facts.
4. **EVALUATE** — Valid + actionable? Unclear? Wrong for this codebase? Conflicts with user intent?
5. **RESPOND** — Per-item: fix, push back with reasoning, or ask a **specific** clarification question. No vague “can you elaborate?”
6. **IMPLEMENT** — Only after the above. One item or coherent group at a time; re-verify after each.

## Forbidden Responses

Do **not** use these **before** you have verified the technical claim in code:

- “You’re absolutely right!”
- “Great point!”
- “Thanks for catching that!” (as a substitute for verification)
- “Let me implement that now”
- Any performative agreement that **signals** you evaluated feedback when you have not

**Allowed after verification:** factual acknowledgment (see below).

## Handling Unclear Feedback

If **any** item is ambiguous, contradictory, or depends on missing context:

- **STOP.** Do not implement that item yet.
- Hold that item and any dependent changes. Continue clearly authorized, independent fixes only after confirming they cannot depend on the unresolved decision; report what remains blocked.
- Ask **targeted** questions that unblock verification (e.g. “Should X preserve behavior Y when Z? The current contract does …”).

**Rule:** Clarify the ambiguous item before implementing it or dependent work. An unrelated clear item need not wait.

## Source-Specific Handling

### From the user

- **Trusted** for product intent and scope — still **ask** if scope or priority is ambiguous.
- **No performative agreement** — if the ask is clear, **skip** flattery and move to **action**.
- If the user contradicts an earlier decision, **surface** the conflict briefly and let them resolve it.

### From external reviewers (human or agent)

- **Check technical correctness** for this stack, repo, and version — generic advice may be wrong here.
- **Check whether the suggestion breaks** existing behavior, public APIs, or migrations.
- **Check reason for current implementation** — grep history/comments; the “obvious” fix may be wrong for legacy or compatibility.
- **Push back** when the suggestion is wrong, over-scoped, or conflicts with documented intent — **factually**, without hostility.

## YAGNI Check

Before “implementing properly” or generalizing because a reviewer suggested it:

- **Grep / search the codebase** for **actual** callers and usage patterns.
- If the abstraction or extra layer is **not justified by real call sites**, treat it as **suspect** unless requirements explicitly demand it.

**Anti-pattern:** Building infrastructure for hypothetical futures because review text implied “best practice.”

## Implementation Order

1. **Separate** unclear items and their dependencies; ask targeted clarification while continuing independent authorized work.
2. **Blocking / Critical** issues that affect correctness, security, or data.
3. **Simple, local fixes** with clear verification.
4. **Complex or cross-cutting fixes** — one coherent slice at a time.
5. **Test** after each meaningful change; do not stack unverified edits.

## When to Push Back

Push back **with concise technical reasoning** (not tone) when the suggestion:

| Situation | Why pushback is valid |
|-----------|------------------------|
| **Breaks existing functionality** or contracts | Regression risk outweighs style preference. |
| **Reviewer lacks context** | They assumed a different system, version, or constraint. |
| **Violates YAGNI** | No real usage; adds maintenance cost. |
| **Technically incorrect** for this language, framework, or runtime | Generic patterns do not always apply. |
| **Legacy / compatibility** | Deliberate oddities may be load-bearing. |
| **Conflicts with explicit user decisions** | Product or architecture call trumps reviewer preference. |

**How to push back:** State the fact (“This path is required because …”), cite code or requirement, propose an alternative if any. Then **move on** — no debate performance.

## Acknowledging Correct Feedback

After **verification**, if the feedback is valid:

- **Good:** “Fixed. [what changed].”
- **Good:** “Good catch — [issue]. Fixed in [file/area].”

**Not acceptable:** “You’re absolutely right!”, “Great point!”, “Thanks for catching that!” as **filler** or **substitute** for describing the fix.

The acknowledgment is **the fix description**, not praise for the reviewer.

## Gracefully Correcting After Pushback

If you pushed back and later **proved yourself wrong**:

- State the correction **factually**: “On review, [X] was incorrect; [Y] is the right behavior. Updated [location].”
- **No** excessive self-flagellation; **no** reverting to performative praise. Correct and proceed.

## Common Mistakes

| Mistake | What goes wrong |
|--------|------------------|
| Agreeing before opening the file | Wrong fix or wrong location; wastes cycles. |
| Implementing unclear comments “to keep momentum” | Inconsistent code; rework; merged bugs. |
| Applying an apparently obvious fix that depends on an unclear item | Partial application; conflicting edits. |
| Treating external review as **orders** | Scope creep, wrong abstractions, broken compatibility. |
| Skipping **grep** / usage check before “proper” design | YAGNI violations; dead abstractions. |
| Stacking many unverified edits | Harder to bisect when tests fail. |
| Performative gratitude instead of verification | Hides that evaluation never happened. |
| Assuming failing tests = reviewer is right | Tests may be stale; verify against requirements. |

## The Bottom Line

**External feedback = suggestions to evaluate, not orders to follow.**

Your standard is **correctness and fit**, not **agreement**. Verify, then implement or push back — every time.
