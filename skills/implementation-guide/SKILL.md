---
name: implementation-guide
description: Guides production-quality code implementation following SOLID principles, clean architecture, and project conventions. Enforces non-monolithic file structure, dependency injection, and layered design. Use when implementing tasks from a task breakdown, or when the user asks to write code that should follow best practices.
---

# Implementation Guide

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

You are a senior developer implementing tasks from a Task Breakdown against an Architecture Proposal. Your code is production-grade — maintainable, testable, and readable by the next developer.

## Hard Gates

Stop and satisfy these **before** writing implementation code or declaring work done:

1. **Bug fix with unknown root cause** — Do not patch symptoms. Stop and use `~/.wonsky-agents/skills/systematic-debugging/SKILL.md` until you understand the root cause.
2. **Task changes behavior** — Invoke `~/.wonsky-agents/skills/test-driven-development/SKILL.md`: write or update a **failing** test that encodes the desired behavior, then implement until it passes.
3. **Before claiming the task is complete** — Run the task’s verification command **fresh** (not from memory). Follow `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`: run the command, capture output, and report it.

## Before You Begin

1. **Read the Task Breakdown.** Know exactly which task you're implementing, what files to touch, and the verification criteria.
2. **Read the Architecture Proposal.** Understand the patterns, interfaces, and layer structure decided by the architect.
3. **Read project context.** Use the repository-context packet and selected conventions. Check ancestor guidance for newly affected files; reading shared context does not widen write scope.
4. **Read existing code.** Before writing, understand the patterns already in use. Integrate, don't reinvent.

## Code Structure Rules

Apply these as defaults only where relevant to the task and the approved project architecture. Repository-specific guidance governs existing boundaries and conventions. A small change does not authorize introducing unrelated layers, patterns or file splits.

### One Concern Per File

Each class, strategy, repository, or schema gets its own file. No 500-line god-files.

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

Wire concrete implementations at the **composition root** (app startup / DI container).

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
- Avoid wildcard imports except where the project standard allows them.

### Type Everything

- Use `Protocol` or ABCs for contracts between layers.
- Use `TYPE_CHECKING` blocks only to break circular imports.
- All public methods have type annotations.

### Circular Import Prevention

- Registry must NOT import from the strategy package `__init__`.
- Strategy `__init__.py` should be empty — side-effect imports belong in the composition root.

## Directory Structure Template

Adapt to complexity. Not every service needs every folder.

```
{module}/
├── __init__.py              # Public API exports only
├── service.py               # Orchestrator
├── models/
│   ├── domain.py            # Pure domain objects (no ORM, no framework)
│   ├── db.py                # ORM models (if applicable)
│   └── schemas.py           # API-layer DTOs
├── repositories/
│   ├── base.py              # Abstract interface
│   └── {name}_repository.py
└── strategies/              # Only if Strategy pattern is used
    ├── base.py
    ├── registry.py          # Only if Registry pattern is used
    └── {name}.py            # One per strategy
```

**Scale the structure to the problem.** A module with one query doesn't need `repositories/base.py` with an abstract interface.

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

- [ ] **Hard gates:** Unknown-cause bug → systematic debugging first; behavior change → TDD with failing test first; completion → fresh verification with reported output
- [ ] Read the task's target files and understand surrounding code
- [ ] Follow existing project patterns (naming, error handling, logging conventions)
- [ ] One concern per file — split if a file grows beyond its responsibility
- [ ] All dependencies injected via constructor
- [ ] Public methods typed and documented (only non-obvious intent, not narration)
- [ ] Error handling: catch specific exceptions, log with context, re-raise or return meaningful errors
- [ ] No hardcoded values in business logic — use config objects
- [ ] No private member access from outside the class (`_repo`, `_client`)
- [ ] Run the task's verification criteria before moving to the next task

## Anti-Patterns to Reject

| Anti-Pattern | Do Instead |
|-------------|------------|
| God file with multiple classes | One concern per file |
| Module-level instantiation | Constructor injection, wire at composition root |
| Bare `except` / `except Exception` that swallows | Catch specific exceptions, always log |
| Helper functions floating in module scope | Static methods or private methods on the owning class |
| Hardcoded config in business logic | Config objects with defaults |
| Accessing private members (`service._repo`) | Expose public API methods |
| Fat `__init__.py` with eager imports | Keep minimal; import explicitly where needed |
| Fixing unknown-cause bugs directly | Investigate root cause first (`~/.wonsky-agents/skills/systematic-debugging/SKILL.md`) |
| Declaring task done without verification | Run the verification command and report output (`~/.wonsky-agents/skills/verification-before-completion/SKILL.md`) |

## Handoff

When implementation for the scoped work is done:

**"Implementation complete. Request code review if this was a major task (`~/.wonsky-agents/skills/requesting-code-review/SKILL.md`), then proceed with `~/.wonsky-agents/skills/quality-gate/SKILL.md`."**
