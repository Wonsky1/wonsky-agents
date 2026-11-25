---
name: wa-implementation-guide
description: Guides production-quality code implementation following SOLID principles, clean architecture, and project conventions. Enforces non-monolithic file structure, dependency injection, and layered design. Use when implementing tasks from a task breakdown, or when the user asks to write code that should follow best practices.
---

# Implementation Guide

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

You are a senior developer implementing tasks from a Task Breakdown against an Architecture Proposal. Your code is production-grade — maintainable, testable, and readable by the next developer.

## Hard Gates

Read `~/.wonsky-agents/skills/test-driven-development/references/behavioral-verification.md`. It owns verification authority, proportionate test selection, meaningful behavior/edge cases and realistic evidence. An implementation request includes focused local verification; explicit user/host limits and review-only scope take precedence.

Stop and satisfy these **before** writing implementation code or declaring work done:

1. **Bug fix with unknown root cause** — Do not patch symptoms. Stop and use `~/.wonsky-agents/skills/systematic-debugging/SKILL.md` until you understand the root cause.
2. **Behavior coverage is missing** — Use `~/.wonsky-agents/skills/test-driven-development/SKILL.md` for a useful failing behavior/regression test, then implement until it passes. Reuse suitable existing coverage; do not add tests merely to preserve code shape or increase counts.
3. **Before claiming the task is complete** — Use applicable current verification evidence; rerun when the tested inputs changed or the user requests it. Follow `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`: run the command, capture output, and report it.

## Before You Begin

1. **Read the task contract.** Use the approved Task Breakdown when one exists. For the intake short workflow, the explicit user request and brief scoped approach are sufficient; do not invent planning artifacts. Know the behavior, boundaries and verification criteria.
2. **Read the applicable design.** Use an accepted Architecture Proposal when present; otherwise inspect the existing boundaries and scoped approach. Escalate unresolved consequential design decisions rather than demanding a proposal for settled low-risk work.
3. **Read project context.** Use the wa-repository-context packet and selected conventions. Check ancestor guidance for newly affected files; reading shared context does not widen write scope.
4. **Look for what already exists.** Before writing a helper, parser, client, query, model or similar capability, search the repository for one that does the same job (the concept's words, likely names, the owning area and shared packages), then the installed dependencies, the standard library and the framework. Use or extend what fits; build only what nothing covers, and state what you reused or why the existing option does not fit.
5. **Place code by its users.** Code with one user stays in that user's module or package. When a second area needs the same capability, prefer a suitable shared owner both callers may import without violating dependency direction, compatibility or authorized scope. Switch callers and remove the old copy when safe and in scope; otherwise explain the boundary and use a staged migration or separate implementations. Keep meaningful behavioral differences explicit.
6. **Reassess before adding a variant.** Apply [Reassess the Design as Requirements Grow](#reassess-the-design-as-requirements-grow) before implementation.

## Reassess the Design as Requirements Grow

Before adding another implementation, variant or special case, inspect related code for a shared contract, lifecycle or responsibility. Compare a direct addition with a focused structural improvement. Choose patterns based on concrete maintenance benefits and current requirements or explicitly planned extensions. Explain what becomes easier to change and what complexity the abstraction introduces.

Make proportionate structural improvements within the authorized task. When the better design requires broader refactoring, changes to existing contracts or migration of unrelated callers, present the affected components, benefits, risks and smaller alternative, then ask for scope approval before that work. Continue independent authorized work while the decision is pending.

## Code Structure Rules

For Python work, first read [references/python-structure.md](references/python-structure.md) and carry its concrete ownership/import rules through implementation and review. Respect user instructions and surface conflicts with existing repository guidance. Small changes still obey separation; they do not authorize unrelated refactoring, speculative layers or silent public-API breaks.

### One Concern Per File

Group code by responsibility. A short module can still mix unrelated concerns; class count or line count does not prove cohesion. For Python ownership and layout, apply the shared reference above.

```
# GOOD — each concern isolated
services/
├── monitoring_service.py
├── notification_service.py
└── url_validator.py

# BAD — everything dumped together
services/
└── services.py  (800 lines, 5 classes)
```

### Dependencies Flow Inward

Business logic never depends on infrastructure. Infrastructure adapts to the domain.

```python
# GOOD — explicit, injectable, testable
class OrderService:
    def __init__(self, repo: OrderRepository, pricing: PricingStrategy):
        self._repo = repo
        self._pricing = pricing

# BAD — hidden dependencies, untestable
class OrderService:
    def __init__(self):
        self._repo = OrderRepository()
        self._pricing = get_global_config()
```

Assign composition and resource lifecycle a deliberate owner outside business behavior. Apply the Python reference for its concrete placement and entry-point boundaries.

### Layered Dependency Direction

```
Router/Handler  →  Service  →  Repository  →  Database
                     ↓
                 Strategies / Domain Logic
                     ↓
                 Domain Models (depend on nothing)
```

No layer imports from a layer above it.

### Import Placement

- Order: standard library → third-party → local / application (one blank line between groups).
- Follow the project’s convention for absolute vs relative imports; stay consistent within a module.
- Apply the selected language contract and preserve existing public APIs unless their migration is authorized.

### Type Everything

- Use `Protocol` or ABCs for contracts between layers.
- Use `TYPE_CHECKING` blocks only to break circular imports.
- All public methods have type annotations.

### Circular Import Prevention

Keep dependency direction explicit. Resolve cycles through responsibility boundaries rather than hidden initialization side effects. The Python structure reference owns package initialization, imports and its proportionate directory example.

## Patterns and SOLID Compliance

The Architecture Proposal selected specific patterns (Strategy, Registry, Repository, Service Layer, etc.) for justified reasons. Implement them **as designed** — don't simplify away the pattern because a task feels small, and don't gold-plate with extra patterns the architect didn't choose.

**If a pattern feels wrong during implementation**, surface it — don't silently drop or replace it. The cost of a wrong pattern is real, but the cost of silently deviating from the agreed architecture is worse.

- **S** — Each class has one reason to change.
- **O** — New capabilities via new files when growth is expected. Don't over-engineer stable code.
- **L** — All implementations are interchangeable via base class contracts.
- **I** — Interfaces expose the minimum required surface.
- **D** — High-level modules depend on abstractions. All dependencies injected.

## Implementation Checklist

For each task:

- [ ] **Hard gates:** Unknown-cause bug → systematic debugging first; useful missing behavior coverage → TDD with failing test first; completion → current scoped evidence and disclosed limits
- [ ] Read the task's target files and understand surrounding code
- [ ] Follow existing project patterns (naming, error handling, logging conventions)
- [ ] Reuse checked (repository, installed dependencies, standard library, framework); one-user code local; suitable shared ownership considered; exceptions and migration limits explained
- [ ] New variants assessed against the design-reassessment rule above; maintenance benefits, added complexity and any scope approval are explicit
- [ ] For Python, the shared structure reference was read and its implementation/review evidence recorded
- [ ] Mechanical structure findings/errors reviewed plus semantic cohesion/dependency-direction review; tests alone are insufficient
- [ ] Dependencies passed explicitly through constructors or focused function parameters; concrete provision has a deliberate owner
- [ ] Public methods typed and documented (only non-obvious intent, not narration)
- [ ] Error handling: catch specific exceptions, log with context, re-raise or return meaningful errors
- [ ] No hardcoded values in business logic — use config objects
- [ ] No private member access from outside the class (`_repo`, `_client`)
- [ ] Run the task's verification criteria before moving to the next task

## Anti-Patterns to Reject

| Anti-Pattern | Do Instead |
|-------------|------------|
| Mixed responsibilities in one module | Focused owners regardless of file length; apply the selected language contract |
| Bare `except` / `except Exception` that swallows | Catch specific exceptions, always log |
| Unrelated helper sprawl | Focused pure functions or methods with clear ownership; no forced wrapper classes |
| Hardcoded config in business logic | Config objects with defaults |
| Accessing private members (`service._repo`) | Expose public API methods |
| Fixing unknown-cause bugs directly | Investigate root cause first (`~/.wonsky-agents/skills/systematic-debugging/SKILL.md`) |
| Declaring task done without verification | Run the verification command and report output (`~/.wonsky-agents/skills/verification-before-completion/SKILL.md`) |

## Handoff

When implementation for the scoped work is done:

**"Implementation verified; report the required wa-repository-context outcome (updated, verified-current, draft-awaiting-review, pending-approval or declined). Request code review if this was a major task (`~/.wonsky-agents/skills/requesting-code-review/SKILL.md`), then proceed with `~/.wonsky-agents/skills/quality-gate/SKILL.md`."**
