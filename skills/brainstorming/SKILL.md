---
name: brainstorming
description: Use when creating or developing, before writing code or implementation plans - refines rough ideas into fully-formed designs through collaborative questioning, alternative exploration, and incremental validation. Don't use during clear mechanical processes.
---

# Brainstorming: Ideas Into Designs

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

Turn rough ideas into an agreed design through dialogue. You **do not** implement until the user has approved the design.

## When not to use this skill

Skip for **clear mechanical work**: single known file change, copy-paste config, obvious one-line fix, or execution of an already-approved plan. Route to implementation or debugging skills instead.

## Hard gate

Do **not** scaffold projects, write production code, or run an implementation workflow until you have **presented the design** and the user has **approved** it. Tiny scopes still get a short explicit design (even a few sentences).

## Process

### 1. Understand the idea

- **Project state first:** skim relevant files, docs, and recent commits so questions are grounded.
- **Oversized requests:** if the user describes several independent subsystems in one breath, stop refining details. Name the slices, suggest build order, and brainstorm **only the first slice** end-to-end; other slices get their own later cycles.
- **Questions:** **one question per message.** Prefer **multiple choice** when possible; open-ended when needed.
- **Focus:** purpose, constraints, success criteria, and explicit non-goals.

### 2. Explore approaches

- Offer **2–3** approaches with trade-offs (cost, risk, time, operability, fit with existing code).
- **Lead with your recommendation** and why.
- Keep options concrete enough to compare; avoid buzzwords without implications.

### 3. Present the design

- When you believe you understand the target, present the design in **sections**.
- **Section length:** scale to complexity — a few sentences when simple, up to **roughly 200–300 words** when nuanced.
- After **each** section, ask whether it looks right before continuing.
- Typical coverage: architecture, main components, data flow, error handling, testing strategy. Omit sections that do not apply.
- **Boundaries:** each unit should have one job, clear interfaces, and be understandable without reading internals. Prefer small, testable units; if existing code is in the way (god objects, tangled deps), call out **targeted** improvements tied to this goal only — no unrelated refactors.

### 4. After the design is approved

1. **Save the design** to:

   `docs/plans/YYYY-MM-DD-<topic>-design.md`

   (If the user or repo uses a different convention, follow their preference.)

2. **Offer optional isolation:** suggest creating or using a git worktree before heavy implementation — see `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md`.

3. **Implementation planning:** when they are ready for step-by-step tasks, use `~/.wonsky-agents/skills/writing-plans/SKILL.md` (assumes zero codebase context in the plan).

## Key principles

- **One question at a time** — avoid question dumps.
- **Multiple choice preferred** — faster answers, clearer decisions.
- **YAGNI ruthlessly** — cut features that do not serve the stated goal.
- **Explore alternatives** — always compare a few paths before settling.
- **Incremental validation** — section-by-section approval beats a wall of text at the end.
- **Stay flexible** — loop back when something does not fit.

## Optional: visual-heavy work

If upcoming choices are inherently visual (layouts, mockups, diagram-heavy comparisons), you may offer a browser-based companion **in its own short message** — never bundled with a clarifying question. If the user declines or the topic stays textual, continue in the editor/chat only.

## Handoff summary

| Next step | Skill |
|-----------|--------|
| Strategic framing, risks, program scope | `~/.wonsky-agents/skills/strategic-planner/SKILL.md` |
| Detailed task plan for implementers | `~/.wonsky-agents/skills/writing-plans/SKILL.md` |
| Worktree / branch isolation | `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md` |

After brainstorming, the usual implementation path is **writing-plans** first, then execution skills — not ad-hoc coding in this same flow.
