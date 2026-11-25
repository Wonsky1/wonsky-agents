---
name: wa-brainstorming
description: Use when creating or developing, before writing code or implementation plans - refines rough ideas into fully-formed designs through collaborative questioning, alternative exploration, and incremental validation. Don't use during clear mechanical processes.
---

# Brainstorming: Ideas Into Designs

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

Turn rough ideas into an agreed design through dialogue. Use the authoritative intake-routing.md reference under unified-dev-pipeline first: clear, reversible, low-risk implementation requests take its short workflow. This skill handles unresolved design decisions.

## When not to use this skill

Skip for **clear mechanical work**: single known file change, copy-paste config, obvious one-line fix, or execution of an already-approved plan. Route to implementation or debugging skills instead.

## Hard gate

Resolve and obtain approval for material design decisions before implementation. Present one coherent design scaled to the uncertainty; reuse an already accepted design and clear end-to-end authority. Do not demand section-by-section confirmation for settled routine work. Instruction/policy edits retain their separate exact approval gate.

## Process

### 1. Understand the idea

- **Project state first:** skim relevant files, docs, and recent commits so questions are grounded.
- **Oversized requests:** if the user describes several independent subsystems in one breath, stop refining details. Name the slices, suggest build order, and brainstorm **only the first slice** end-to-end; other slices get their own later cycles.
- **Questions:** inspect available evidence first, then batch related unresolved decisions in one concise message. Prefer a recommended choice with concrete trade-offs; skip questions already answered by the task or repository.
- **Focus:** purpose, constraints, success criteria, and explicit non-goals.

### 2. Explore approaches

- Offer **2–3** approaches with trade-offs (cost, risk, time, operability, fit with existing code).
- **Lead with your recommendation** and why.
- Keep options concrete enough to compare; avoid buzzwords without implications.

### 3. Present the design

- When you believe you understand the target, present the design in **sections**.
- **Section length:** scale to complexity — a few sentences when simple, up to **roughly 200–300 words** when nuanced.
- Present related sections together and ask for one design decision when needed. Use intermediate checkpoints only when the user requests them or a decision blocks later design.
- Typical coverage: architecture, main components, data flow, error handling, testing strategy. Omit sections that do not apply.
- **Boundaries:** each unit should have one job, clear interfaces, and be understandable without reading internals. Prefer small, testable units; if existing code is in the way (god objects, tangled deps), call out **targeted** improvements tied to this goal only — no unrelated refactors.

### 4. After the design is approved

1. **Save the design** to:

   `docs/plans/YYYY-MM-DD-<topic>-design.md`

   (If the user or repo uses a different convention, follow their preference.)

2. **Offer optional isolation:** suggest creating or using a git worktree before heavy implementation — see `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md`.

3. **Implementation planning:** when they are ready for step-by-step tasks, use `~/.wonsky-agents/skills/writing-plans/SKILL.md` (assumes zero codebase context in the plan).

## Key principles

- **Batch related decisions** — keep questions concise and avoid serial clarification of already settled details.
- **Multiple choice preferred** — faster answers, clearer decisions.
- **YAGNI ruthlessly** — cut features that do not serve the stated goal.
- **Explore alternatives** — always compare a few paths before settling.
- **Proportionate validation** — one coherent review for a small design; meaningful checkpoints for uncertain or substantial work.
- **Stay flexible** — loop back when something does not fit.

## Optional: visual-heavy work

If upcoming choices are inherently visual (layouts, mockups, diagram-heavy comparisons), you may offer a browser-based companion **in its own short message** — never bundled with a clarifying question. If the user declines or the topic stays textual, continue in the editor/chat only.

## Handoff summary

| Next step | Skill |
|-----------|--------|
| Strategic framing, risks, program scope | `~/.wonsky-agents/skills/strategic-planner/SKILL.md` |
| Detailed task plan for implementers | `~/.wonsky-agents/skills/writing-plans/SKILL.md` |
| Worktree / branch isolation | `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md` |

After brainstorming, the usual implementation path is **wa-writing-plans** first, then execution skills — not ad-hoc coding in this same flow.
