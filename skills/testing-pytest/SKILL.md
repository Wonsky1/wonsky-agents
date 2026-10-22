---
name: testing-pytest
description: Creates pytest unit tests for changed files. Detects staged/unstaged git changes, analyzes modified functions, mocks dependencies, runs tests, and fixes source code when tests fail on expected behavior. Use when writing pytest tests, adding test coverage, or when delegated by the Quality Gate skill.
---

# Pytest Test Creator

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

## Philosophy

Tests verify **what the code should do**, not what it currently does. If a test for correct behavior fails, **fix the source code**, not the test.

## Scope

Only test files that have been changed. Don't waste time testing unchanged code.

## Workflow

Copy this checklist and track progress:

```
Test Creation Progress:
- [ ] Step 0: Detect changed files
- [ ] Step 1: Understand the targets
- [ ] Step 2: Identify the contract
- [ ] Step 3: Plan test cases
- [ ] Step 4: Set up mocks and fixtures
- [ ] Step 5: Write tests
- [ ] Step 6: Run tests
- [ ] Step 7: Triage failures
```

### Step 0: Detect changed files

Identify which source files have been modified and need tests.

```bash
# Staged changes
git diff --cached --name-only --diff-filter=ACM -- '*.py'

# Unstaged changes
git diff --name-only --diff-filter=ACM -- '*.py'

# Untracked new files
git ls-files --others --exclude-standard -- '*.py'
```

Combine results and **filter out**:
- Test files (`test_*.py`, `*_test.py`, `conftest.py`)
- Migration files, `__init__.py` with no logic, config-only files with no testable behavior

The remaining list is your **target set**.

If the user explicitly names a file or function, use that instead (skip auto-detection).

For each target file, run `git diff` on it to see **what changed** — focus tests on new/modified functions:

```bash
git diff --cached -- path/to/file.py
git diff -- path/to/file.py
```

### Step 1: Understand the targets

For each changed source file, deeply examine the modified functions or classes:

1. **Read the function** — signature, parameters, return type, docstring.
2. **Read its callers** — search for usages to understand what consumers expect.
3. **Read its dependencies** — trace imports, database calls, HTTP clients, service calls.
4. **Read related models/schemas** — understand data structures flowing in and out.

Focus on **changed portions**. If a file has 20 functions but only 2 were modified, prioritize those 2.

### Step 2: Identify the contract

Define the function's behavioral contract:

- **Inputs**: Valid inputs? Edge cases (empty, None, boundary)?
- **Outputs**: Expected shape/type/values for given inputs?
- **Side effects**: DB writes? API calls? Events emitted?
- **Error handling**: Behavior on bad input? On dependency failure?
- **Invariants**: What must always be true before and after the call?

If docstrings or callers reveal intent that contradicts the implementation, the implementation is the bug — note it for Step 7.

### Step 3: Plan test cases

| Category | Examples |
|----------|----------|
| **Happy path** | Typical valid input producing expected output |
| **Edge cases** | Empty collections, zero values, None, boundary values |
| **Error paths** | Invalid input, dependency failures, timeouts |
| **State transitions** | Correct status changes, data transformations |
| **Variants** | Per-category or per-type behavior if applicable |

Each test asserts **one logical behavior**. Descriptive names: `test_<what>_<condition>_<expected>`.

### Step 4: Set up mocks and fixtures

**Mock everything external.** The unit under test runs in complete isolation:

- **Database sessions** → mock or fake in-memory store
- **HTTP clients / API calls** → `AsyncMock` or `MagicMock`
- **File system** → `tmp_path` fixture or mocks
- **Time-dependent logic** → freeze with deterministic values
- **Environment variables** → `monkeypatch.setenv`
- **Module-level singletons** → patch before import if needed

Check if the project already has a `conftest.py` with reusable fixtures before creating new ones.

Use `make_{entity}` fixture factories with sensible defaults:

```python
def make_task(*, chat_id="123", url="https://example.com", name="test", **overrides):
    defaults = dict(chat_id=chat_id, url=url, name=name)
    defaults.update(overrides)
    return MonitoringTask(**defaults)
```

### Step 5: Write tests

1. **Use `pytest` style** — plain functions or classes, `@pytest.mark.asyncio` for async.
2. **Arrange-Act-Assert** — clear separation.
3. **One logical assertion per test** — multiple `assert` fine if verifying same behavior.
4. **No implementation leakage** — don't assert on private internals or execution order unless that IS the contract.
5. **Use parametrize** for same logic across multiple inputs:

```python
@pytest.mark.parametrize("input_val,expected", [
    (0, "zero"),
    (1, "one"),
    (-1, "negative"),
])
def test_categorize(input_val, expected):
    assert categorize(input_val) == expected
```

6. **Test file placement** — before creating a new file, check for existing test files covering the same module:

   **Add to existing file when:**
   - It tests the same module/class
   - Fixtures and mocks are compatible

   **Create new file when:**
   - No existing test file covers this module
   - Different import chain or fundamentally different mock patterns

   Naming — mirror source structure: `src/services/foo.py` → `tests/services/test_foo.py`

### Step 6: Run tests

Detect the project's test runner:

| Signal | Command |
|--------|---------|
| `uv.lock` exists | `uv run pytest ...` |
| `poetry.lock` exists | `poetry run pytest ...` |
| `Pipfile.lock` exists | `pipenv run pytest ...` |
| None of the above | `pytest ...` |

**Only run test files you created/modified:**

```bash
<runner> pytest path/to/test_file.py -v
```

Specific test:

```bash
<runner> pytest path/to/test_file.py::TestClassName::test_method -v
```

### Step 7: Triage failures

For each failing test:

```
Test fails
  ├── Test expectation wrong (misunderstood contract) → Fix the test
  ├── Mock setup wrong (wrong return type, missing attr) → Fix the mock
  └── Source code doesn't meet its contract → Fix the source code
```

**If the source code is wrong, fix the source code, not the test.**

After fixing, re-run your tests plus any existing tests for the same module to avoid regressions.

## Anti-Patterns

- **Snapshot testing the implementation** — Don't assert on whatever it returns today. That tests nothing.
- **Testing private methods directly** — Test the public interface.
- **Mocking the unit under test** — Mock its dependencies, not the function you're testing.
- **Ignoring async** — If the function is `async`, use `@pytest.mark.asyncio`.
- **Hardcoding flaky values** — Don't use `datetime.utcnow()` in assertions.

## Related skills

- Discipline (test first, verify failure): `~/.wonsky-agents/skills/test-driven-development/SKILL.md`
- Mocks and production boundaries: `~/.wonsky-agents/skills/testing-anti-patterns/SKILL.md`
