---
name: strict-code-quality-review
description: Use when the user asks for a thermo-nuclear, thermonuclear, harsh, deep maintainability, architecture, abstraction, spaghetti-code, large-file, or code quality review - applies an unusually strict structural quality bar.
---

# Strict Code Quality Review

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

Use this skill when reviewing code for maintainability, abstraction quality, modularity, and long-term codebase health. This is stricter than a normal correctness review: passing tests and working behavior are not enough if the change makes the codebase meaningfully harder to reason about.

For Python reviews, first read `~/.wonsky-agents/skills/implementation-guide/references/python-structure.md` and inspect its required evidence. Pass that reference with delegated Python review tasks.

## Core Standard

Look for ways to preserve behavior while making the implementation smaller, more direct, and more obvious. Prefer changes that delete concepts, branches, wrappers, and special cases over changes that merely rearrange the same complexity.

## Review Questions

For every meaningful change, ask:

- Is there a simpler reframing that would remove branches, flags, helper layers, or modes?
- Did the diff add ad-hoc conditionals into an already busy flow?
- Is the logic in the canonical layer, package, or module that owns the concept?
- Does the change reuse existing helpers and patterns, or introduce a bespoke near-duplicate?
- Did a cohesive module become more coupled, stateful, or harder to scan?
- Did a file cross the repository's healthy size boundary? If no project rule exists, treat crossing 1000 lines as a strong smell.
- Are repeated conditionals, nullable modes, casts, `any` / `unknown`, or optional parameters hiding a missing model or unclear boundary?
- Does the abstraction earn its keep, or is it just a thin wrapper around simple behavior?
- Is orchestration unnecessarily sequential when independent work could be simpler and clearer in parallel?
- Can related updates be made more atomic so partial state is harder to create?

## Do Not Lose Normal Review Coverage

The strict maintainability lens is additive. Do not let it replace the basics from a normal PR review:

- Does the implementation satisfy the stated requirements and acceptance criteria?
- Did the diff introduce a behavioral regression, data loss risk, or broken edge case?
- Are tests present for the changed behavior, and do they verify behavior rather than mocks?
- Are auth, permissions, input validation, secrets, SQL/query construction, and error leakage still safe?
- Are migrations, API contracts, config examples, and downstream consumers updated where needed?
- Did the PR add unrequested scope that should be split or removed?

If a correctness, security, or requirement issue exists, prioritize it alongside structural findings. A clean design that implements the wrong behavior is still a blocker.

## Flag Aggressively

- Structural regressions that make future changes harder.
- Missed simplifications where a cleaner model could delete whole categories of complexity.
- Special-case branches scattered through shared or unrelated flows.
- Feature logic leaking into general-purpose modules.
- Generic or magical handling that hides a simple data shape.
- Thin wrappers, identity abstractions, or pass-through helpers that add indirection without clarity.
- Cast-heavy or loosely typed boundaries where an explicit model would simplify the flow.
- Copy-pasted logic instead of a canonical helper or focused extraction.
- Large-file growth, especially when the new code has a natural module boundary.
- Refactors that move complexity around without reducing how much a reader must hold in their head.

## Preferred Remedies

- Delete unnecessary indirection instead of polishing it.
- Reframe the state model so conditionals disappear.
- Move logic to the layer or module that already owns the concept.
- Extract a focused helper, pure function, component, or service only when it reduces real complexity.
- Replace condition chains with an explicit typed model, dispatcher, policy object, or state machine when that makes the flow clearer.
- Separate orchestration from business logic.
- Collapse duplicate branches into one direct flow.
- Reuse the canonical helper instead of adding a near-duplicate.
- Make type boundaries explicit so control flow does not rely on silent fallback.
- Parallelize independent work when it improves clarity as well as performance.
- Make related updates atomic when partial state would be hard to reason about.

## Output Expectations

Lead with high-conviction findings. Order them by impact:

1. Structural regressions.
2. Missed opportunities for major simplification.
3. Spaghetti or branching complexity growth.
4. Boundary, layer, abstraction, or type-contract problems.
5. File-size and decomposition concerns.
6. General legibility and maintainability concerns.

Do not flood the review with cosmetic nits when structural issues exist. For each finding, include the file or diff location, the concrete issue, why it matters, and the cleaner direction.

## Approval Bar

Do not approve a change merely because behavior seems correct. Treat these as presumptive blockers unless clearly justified:

- The change preserves incidental complexity when a plausible simplification would delete it.
- The diff pushes a file past the repository's healthy size boundary without a strong reason.
- New feature checks are scattered across shared code instead of isolated behind a clear owner.
- The design adds unnecessary wrappers, casts, optionality, or fallback behavior that obscures the invariant.
- Logic lands in the wrong layer or duplicates an existing canonical helper.

If the review is for a public PR, still follow the posting workflow and voice calibration in `~/.wonsky-agents/skills/github-pr-review/SKILL.md`.
