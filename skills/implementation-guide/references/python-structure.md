# Python module ownership and imports

Read before designing, implementing or reviewing Python changes, including work delegated to an executor. This is the shared Python structure contract. User instructions take precedence. An observed legacy pattern does not waive these defaults; surface a conflict and propose a scoped migration before breaking an existing public API.

## Assign owners before coding

Name the actual files that own data models, behavior, infrastructure access and dependency provision for the affected feature. Group by responsibility, not by line count or number of classes. A short module mixing these responsibilities is still mixed. Keep useful existing boundaries; introduce only directories with real contents. Focused pure functions are valid: do not wrap them in classes to satisfy a style rule or add speculative protocols/repositories/strategies.

- **Models:** place domain records, DTOs, validation/persistence schemas and configuration data types under the owning package's `models/`, in focused modules such as `models/invoice.py` or `models/settings.py`. Related models may share a concern module. Services, routers, dependencies and app entry points import models instead of defining them above behavior. Model declarations in tests may remain with test fixtures. Interfaces/protocols belong at the appropriate contract boundary and need no model label solely because they are types.
- **Dependencies:** provider functions, client/session construction, resource lifetime wiring and service/repository assembly belong in `dependencies/<concern>.py`, for example `database.py`, `authentication.py`, `clients.py` and `invoices.py`. Separate groups as they acquire distinct responsibilities; do not move all wiring into a new catch-all module. `app.py` coordinates startup, registration and lifespan by calling imported wiring; routers declare transport behavior and consume imported providers. Neither owns provider implementations or concrete resource construction. Do not create dependencies modules when the feature has no dependency provision.
- **Behavior:** cohesive service functions/classes consume explicit inputs and dependencies. Request parsing, business decisions, persistence and provider construction do not belong in one module. Shared means demonstrably shared, not a reason to create a `utils.py` dumping ground.

```text
invoices/
  __init__.py                 # Empty or package docstring only
  models/invoice.py           # Related invoice data types
  services/invoice_service.py # Invoice behavior
  dependencies/database.py    # Session provision, if needed
  dependencies/invoices.py    # Invoice service assembly, if needed
  routers/invoices.py         # Transport, consuming imported providers
```

This example is an ownership map, not a required scaffolding generator. A small function needs no service class; an in-memory implementation needs no invented database/repository layer.

## Direct imports

Import symbols from the module that defines them, for example `from invoices.models.invoice import Invoice`. Package `__init__.py` files are empty or package documentation only. Do not add re-export imports, `__all__`, lazy export facades, registry side effects or application initialization there. Never add wildcard imports (`from x import *`), even when legacy code uses them. Preserve a published legacy package API until its migration is explicitly authorized; report its remaining violation and compatibility impact instead of silently breaking callers or claiming a clean result.

## Required implementation and review evidence

Before reporting ready, name the model and dependency owner files (or explain why that responsibility is absent), inspect dependency direction, and review each changed module for mixed concerns. Check initializers and direct imports. Small changes still require this check; passing behavior tests, lint or typing does not prove structure. Fix in-scope violations; report pre-existing out-of-scope violations separately and request scope changes only when needed for correctness.

Use the read-only helper for mechanical checks on explicit changed Python files, including untracked files and changed initializers:

```sh
python3 <loaded-implementation-guide-directory>/scripts/check_structure.py --repo-root /repository /repository/path/to/changed.py /repository/path/to/package
```

Resolve the script relative to the loaded skill. It parses AST without importing target code, changing files, installing packages or generating documentation. Findings include file, line, rule and message; exit 0 means the checked rules found nothing, 1 means findings, and 2 means input/read/parse failure. Retain all findings and errors. The helper is deliberately limited to recognizable declarations/construction patterns; unrecognized models, dependency lifecycle and semantic cohesion still require review. A clean scan is not architecture approval. It does not authorize scanning beyond the declared read scope or rewriting legacy APIs.
