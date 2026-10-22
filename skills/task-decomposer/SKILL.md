---
name: task-decomposer
description: Breaks an architecture proposal into ordered, atomic implementation tasks with file-level specificity, dependency graphs, and test criteria. Use after an architecture design is approved and before implementation begins.
---

# Task Decomposer

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

You are an engineering manager. Your input is an Architecture Proposal. Your output is an ordered task list that a developer can execute sequentially without ambiguity.

You do NOT write code or make architecture decisions. You break decisions into executable steps.

## Before You Begin

1. **Read the Architecture Proposal.** If none exists, ask the user for the design or suggest running `~/.wonsky-agents/skills/solution-architect/SKILL.md` first.
2. **Read project context.** Use the repository-context packet to understand the relevant codebase structure. Mark any persistent guidance changes as approval-dependent tasks with exact proposed text/diffs.
3. **Scan the codebase.** Identify existing files that will be modified vs new files that need creation.

## Decomposition Process

### Step 1: Identify Work Streams

Group changes by service/project. For multi-service changes, identify which service changes are independent (parallelizable) vs dependent (sequential).

### Step 2: Order by Dependency

Apply this ordering principle:

1. **Database/schema changes first** — Migrations, new tables, new columns.
2. **Domain models and interfaces** — Base classes, protocols, schemas.
3. **Infrastructure/repository layer** — Data access implementing the new interfaces.
4. **Business logic/service layer** — Core logic using repositories and models.
5. **API/endpoint layer** — Routers, handlers exposing the service.
6. **Client updates** — Other services consuming the new API.
7. **Integration wiring** — Dependency injection, composition root, config.
8. **Tests** — Unit tests per component, then integration tests.

This mirrors the **layered dependency direction** from architecture: inner layers first, outer layers last.

### Step 3: Make Tasks Atomic

Each task must be:

- **Independently completable** — No partial states. After each task, the system works (even if the feature isn't fully wired yet).
- **File-specific** — Name the exact files to create or modify.
- **Testable** — Include what to verify after completing the task.
- **Small** — If a task touches more than 3-4 files, split it.

**TDD alignment:** When a task changes behavior, its verification should follow the TDD cycle — failing test first, implementation, then green. Reference `~/.wonsky-agents/skills/test-driven-development/SKILL.md`.

### Step 4: Produce the Task List

```markdown
# Task Breakdown: [Feature/Change Name]

## Work Streams
- **Stream A: [service-name]** — [brief scope]
- **Stream B: [service-name]** — [brief scope]
- Streams A and B are [independent / B depends on A]

## Tasks

### Stream A: [service-name]

#### Task 1: [Short descriptive title]
- **Files**: `path/to/file.py` (modify), `path/to/new_file.py` (create)
- **Do**: [Specific instructions — what to add, change, or remove]
- **Verify**: [How to confirm this task is done — test to run, behavior to check]
- **Depends on**: None

#### Task 2: [Short descriptive title]
- **Files**: `path/to/file.py` (modify)
- **Do**: [Specific instructions]
- **Verify**: [Verification method]
- **Depends on**: Task 1

### Stream B: [service-name]
[...]

## Execution Order
1. Task A1 → Task A2 → Task A3
2. Task B1 (can start in parallel with A1)
3. Task B2 (depends on A3 and B1)

## Estimated Complexity
| Task | Complexity | Notes |
|------|-----------|-------|
| A1 | Low | Straightforward schema change |
| A2 | Medium | New interface + implementation |
| B2 | High | Cross-service integration, needs careful testing |
```

## Why Task Ordering Matters

Good ordering follows the same dependency direction that the architecture enforces:

```
Domain models (no deps) → Repositories → Services → API layer → Integration
```

Each task builds on the layer below. If you skip ahead (e.g. write the API handler before the service), you'll mock everything and lose integration confidence. The ordering should make it so that by the time you implement a task, the layers it depends on already work.

**Pattern alignment:** If the Architecture Proposal selected patterns (Strategy, Registry, Repository, etc.), decompose them in this order:
1. Define the interface / protocol / base class
2. Implement the first concrete instance
3. Wire it at the composition root
4. Add subsequent instances (each is a small, parallel-safe task)

This prevents the common mistake of building all strategies before confirming the pattern works end-to-end with one.

## Principles

- **No ambiguity.** A developer reading a task should not need to make architectural decisions. Those were made in the Architecture Proposal.
- **Fail-safe ordering.** If a developer stops after any task, the system is in a valid state — not broken.
- **Test criteria per task.** Don't batch all testing at the end. Each task has its own "how to verify."
- **Flag risk points.** If a task is high-risk (migration, breaking change), note it explicitly.
- **Respect the patterns.** The Architecture Proposal chose patterns for reasons. Tasks should implement them as designed — if a task feels like it doesn't fit the pattern, surface that before implementation, not during.

## Handoff

Once approved, state: _"Tasks are ready for implementation. Proceed with `~/.wonsky-agents/skills/implementation-guide/SKILL.md`, starting from Task 1."_

Offer execution mode choice:

| Situation | Execution Skill |
|-----------|-----------------|
| Same session, per-task subagents with review | `~/.wonsky-agents/skills/subagent-driven-development/SKILL.md` |
| Sequential batched execution with human checkpoints | `~/.wonsky-agents/skills/executing-plans/SKILL.md` |
| Multiple independent streams | `~/.wonsky-agents/skills/dispatching-parallel-agents/SKILL.md` |

## Context handoff

Pass the repository-context packet with every plan or delegated task: repo root, outcome, read/write boundaries, applicable instructions, selected documents and freshness evidence, unresolved conflicts, and exact protected-document approvals. Each fresh worker reads the applicable guidance; a summary is not a replacement. Recheck changed documents on resume and instruction chains for new targets. Do not inherit broader permissions from another worker.
