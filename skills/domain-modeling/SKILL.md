---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
---

# Domain Modeling

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

Actively build and sharpen the project's domain model as you design. This is the *active* discipline — challenging terms, inventing edge-case scenarios, and proposing precise glossary and decision changes when they crystallise, then writing factual drafts for review while preserving approved meanings and historical decisions. (Merely *reading* `CONTEXT.md` for vocabulary is not this skill — that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create useful factual glossary or decision-history drafts when confirmed content exists, using repository-context draft markers and user review. Link established domain documents rather than duplicate them. Existing approved definitions, active policies and historical decisions are preserved; changes to them require exact approval before writing.

## During the session

### Challenge against the glossary

When a user term conflicts with CONTEXT.md, surface the discrepancy. If the user has already resolved the meaning, use that meaning and propose updating the stale glossary; do not reopen the settled decision. Otherwise ask for clarification: "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Propose CONTEXT.md changes

When a term is resolved, use [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) to write a clearly marked draft entry without changing an existing approved definition. Show the actual path/diff, evidence and scope, and ask whether the meaning and coverage are correct. Changes to established definitions require the exact pre-write approval gate. Batch related review items and reuse existing exact approvals.

`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use [ADR-FORMAT.md](./ADR-FORMAT.md) for a clearly marked factual draft of the actual decision and ask the user to review it. Record genuinely unresolved choices as proposals, not accepted decisions. Changing, moving or removing an existing historical ADR or activating a new policy requires exact approval; preserve historical rationale.
