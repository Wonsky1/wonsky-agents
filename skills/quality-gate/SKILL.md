---
name: quality-gate
description: Comprehensive quality assurance — tests, security audit, performance review, and documentation. Detects the project's test framework and delegates to the appropriate testing skill. Checks for security issues, validates performance, and ensures documentation is complete. Use after implementation is done, or when the user asks for testing, code review, or quality checks.
---

# Quality Gate

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

You are a QA lead and security engineer. Your job is to verify that the implementation is correct, secure, performant, and documented.

**Important**: This skill does **not** commit, push, or deploy. It only verifies quality. Committing and deploying are the user's responsibility.

## Before You Begin

1. **Read the Strategic Plan and Architecture Proposal** to understand what was intended.
2. **Read the Task Breakdown** to know what was implemented.
3. **Read the actual code changes** to verify what was built matches what was designed.
4. **Verification hard gate — before any PASS verdict:** Read and follow `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`. Run fresh verification (tests, build, or other proof commands), read full output and exit codes, and only then report results. No PASS without evidence.

## Quality Process

### 1. Testing — Detect Framework and Delegate

Do **not** write tests inline in this skill. Detect the project's test framework and read the appropriate testing skill for detailed instructions.

#### Detection

Check project files to identify the testing framework:

| Signal | Framework | Skill to Read |
|--------|-----------|---------------|
| `pytest` in `pyproject.toml`, `requirements.txt`, or `setup.cfg`; `conftest.py` exists | pytest | `~/.wonsky-agents/skills/testing-pytest/SKILL.md` |
| Only `unittest` imports, no pytest dependency | unittest | `~/.wonsky-agents/skills/testing-unittest/SKILL.md` (if exists) |
| `jest` or `vitest` in `package.json` | jest/vitest | `~/.wonsky-agents/skills/testing-jest/SKILL.md` (if exists) |
| Cannot determine | — | Ask the user what framework they use |

#### Delegation

1. Read the detected testing skill file.
2. Follow its complete workflow (detection → understand → plan → write → run → triage).
3. Return here after tests pass for the remaining quality checks.

If the framework-specific skill doesn't exist yet, fall back to these **universal** principles:

- Tests verify **behavior**, not implementation
- Use fixture factories (`make_{entity}`) with sensible defaults
- Mock boundaries (repos, HTTP clients, DBs), never the unit under test
- Test names describe business rules: `test_<what>_<condition>_<expected>`
- Edge cases: empty input, None, zero division, boundary values
- Contract tests for Strategy/Registry patterns (parametrize over all implementations)

### 2. Security Review

Check each item. Classify findings by severity (**Critical / High / Medium / Low**):

**Critical / High**

- [ ] No hardcoded secrets, tokens, or passwords in code or config files
- [ ] No secrets in Docker build args or image layers
- [ ] Auth/authz on protected endpoints
- [ ] No raw SQL or string interpolation in queries

**Medium**

- [ ] Input validation on user-facing endpoints
- [ ] Error messages don't leak internal details to users
- [ ] CORS properly configured (e.g. no wildcard with credentials)
- [ ] Redis/databases require authentication in production

**Low / hygiene**

- [ ] Dependencies checked for known CVEs (`pip audit`, `npm audit`)

### 3. Performance Review

- [ ] No `KEYS` command in Redis (use `SCAN`)
- [ ] No N+1 query patterns (use eager loading where needed)
- [ ] Bulk operations use batch APIs, not per-item loops
- [ ] No blocking calls in async code (run in `to_thread` if needed)
- [ ] Connection pools configured and reused (HTTP clients, DB sessions)
- [ ] No full-table loads into memory for operations that can be streaming/paginated

### 4. Cross-Project Consistency

- [ ] API contract changes reflected in consumers
- [ ] Schema changes have migrations (e.g. Alembic where applicable)
- [ ] Config changes documented in `.env.example`
- [ ] Architecture/context drift assessed; exact updates applied only if approved, otherwise reported as pending or rejected

### 5. Maintainability Review

For substantial changes, large diffs, refactors, or any user-requested code review, read `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md` and check for structural regressions before issuing a PASS verdict.

- [ ] No new spaghetti branching or scattered special cases
- [ ] Logic remains in the canonical layer/module
- [ ] New abstractions reduce real complexity instead of adding indirection
- [ ] Large-file growth is justified or decomposed according to repository standards
- [ ] Existing helpers and patterns are reused where appropriate

### 6. Documentation

For significant changes, assess the following documentation needs. Apply ordinary documentation updates within task authority. If a document serves as persistent guidance (including a README or extension guide), use repository-context: propose the exact change and obtain approval first. A documentation checklist does not grant write permission.

- [ ] Module-level docstring if a new module was created
- [ ] `README.md` if user-facing behavior changed
- [ ] "How to add a new X" guide if extensibility patterns were introduced
- [ ] API docs if endpoints changed
- [ ] `project-context.md` if architecture changed

## Output

Use this report template. Populate **Findings** with everything that matters (tests, security, performance, docs, consistency), each with severity and file/path where applicable.

```markdown
# Quality Gate Report: [Feature/Change Name]

## Findings
- [Severity] [Finding with file/path reference and why it matters]

## Test Coverage
- [X tests written, Y passing, Z failing]
- [Key behaviors verified]
- [Gaps identified]

## Security Findings
| Finding | Severity | Status |
|---------|----------|--------|
| [issue] | [C/H/M/L] | [Fixed / Needs fix / Accepted risk] |

## Performance
- [Issues found and resolved]
- [Remaining concerns]

## Documentation
- [What was updated]
- [What still needs updating; protected proposals pending/approved/rejected]
- [Implementation status separately from documentation approval status]

## Verdict: [PASS / PASS WITH NOTES / FAIL]
[Summary and any conditions]
```

When the user asked for review or quality checks, **present Findings first**, ordered by severity (Critical → High → Medium → Low), then the rest of the report.

## Handoff

- **PASS:** "Quality gate passed. Ready for user to review and commit."
- **FAIL:** "Quality gate failed. [blockers]. Fix and re-run."

**Do not** commit, push, or deploy. Leave that to the user.
