---
name: quality-gate
description: Comprehensive quality assurance — tests, security audit, performance review, and documentation. Detects the project's test framework and delegates to the appropriate testing skill. Checks for security issues, validates performance, and ensures documentation is complete. Use after implementation is done, or when the user asks for testing, code review, or quality checks.
---

# Quality Gate

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

You are a QA lead and security engineer. Your job is to verify that the implementation is correct, secure, performant, and documented.

**Important**: This skill does **not** commit, push, or deploy. It only verifies quality. Committing and deploying are the user's responsibility.

## Before You Begin

Establish the requested mode first. **Review-only** means inspect and report; do not edit source/tests or run tests unless the user requested test/verification execution. **Verification** runs authorized existing checks. **Test creation/remediation** requires the corresponding user request and write scope. A delegated testing skill inherits this mode and cannot enlarge it.

1. **Read the Strategic Plan and Architecture Proposal** to understand what was intended.
2. **Read the Task Breakdown** to know what was implemented.
3. **Read the actual code changes** to verify what was built matches what was designed.
4. **Verification hard gate — before any PASS verdict:** Read and follow `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`. Bind evidence to the exact change set, environment and claim; read complete results and exit codes. Reuse unchanged evidence and run only authorized checks. A read-only review may report findings, but cannot claim runtime checks passed when none ran.

## Quality Process

### 1. Testing — Detect Framework and Delegate

Reuse the language/toolchain and commands already resolved by `unified-dev-pipeline` and the actual project configuration. Do not redetect Python or force a listed framework onto Swift, Go, Rust, C++ or other projects. If unresolved, inspect manifests, CI and documented commands; ask only when this remains ambiguous. Test-writing delegation applies only in the authorized test-creation mode.

#### Detection

Check project files to identify the testing framework:

| Signal | Framework | Skill to Read |
|--------|-----------|---------------|
| `pytest` in `pyproject.toml`, `requirements.txt`, or `setup.cfg`; `conftest.py` exists | pytest | `~/.wonsky-agents/skills/testing-pytest/SKILL.md` |
| Only `unittest` imports, no pytest dependency | unittest | `~/.wonsky-agents/skills/testing-unittest/SKILL.md` (if exists) |
| `jest` or `vitest` in `package.json` | jest/vitest | `~/.wonsky-agents/skills/testing-jest/SKILL.md` (if exists) |
| Swift, Go, Rust, C++, JVM or another toolchain | Project-native runner | Use the resolved Language Adapter and actual project/CI command |
| Cannot determine after inspecting project evidence | — | Ask the user for the missing runner information |

#### Delegation

1. Pass the requested mode, scope, resolved commands and existing evidence to the testing worker.
2. In review-only mode, inspect contracts, coverage and existing results; report gaps without writing/fixing/running tests.
3. In verification mode, run the authorized existing checks. In test-creation mode, follow the appropriate write/run/triage workflow within scope.
4. Return all failures, skipped checks and limitations; never turn unavailable checks into a pass.

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
- [ ] Untrusted values use parameter binding; dynamic identifiers use a validated allowlist or safe query-builder API. Inspect unsafe interpolation and actual injection paths. Parameterized SQL itself is not a vulnerability.

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
- [ ] Factual architecture/context drafts inspected and user review requested; existing rules/proposed policies changed only with exact approval

### 5. Maintainability Review

For Python changes, read `~/.wonsky-agents/skills/implementation-guide/references/python-structure.md` and inspect the evidence required by that contract in the actual authorized review input. Run its read-only checker only when execution is authorized and explicit matching changed Python paths are available within the read scope. A supplied diff is reviewable without a checkout or command execution: inspect what it shows, report that the checker was not run and state any missing-file/context limits. Never substitute another checkout or widen scope to obtain a scan. A clean scan is not semantic architecture proof. Unresolved in-scope structural violations prevent a ready verdict; report legacy/out-of-scope findings and compatibility constraints separately.

For substantial changes, large diffs, refactors, or any user-requested code review, read `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md` and check for structural regressions before issuing a PASS verdict.

- [ ] No new spaghetti branching or scattered special cases
- [ ] Logic remains in the canonical layer/module
- [ ] New abstractions reduce real complexity instead of adding indirection
- [ ] Large-file growth is justified or decomposed according to repository standards
- [ ] Existing helpers and patterns are reused where appropriate

### 6. Documentation

For every repository engineering delivery, assess the required repository-context outcome and the following relevant documentation needs. Apply ordinary documentation updates within task authority. Use repository-context to write useful factual drafts and ask the user to review them; changes to existing rules and proposed policies need exact approval before writing or activation. A documentation checklist does not grant write permission.

- [ ] Module-level docstring if a new module was created
- [ ] `README.md` if user-facing behavior changed
- [ ] "How to add a new X" guide if extensibility patterns were introduced
- [ ] API docs if endpoints changed
- [ ] Existing context index and cohesive topics (reuse established paths; create missing useful factual drafts and ask for user review)
- [ ] Context outcome includes actual paths/evidence: updated, verified-current, draft-awaiting-review with an explicit review request, pending-approval for exact policy proposals, or user-declined

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
- [Actual context outcome, paths/evidence, factual draft review request and separate exact policy approvals]
- [Implementation status separately from documentation approval status; pending means the combined delivery remains incomplete]

## Verdict: [PASS / PASS WITH NOTES / FAIL / REVIEW ONLY]
[Use REVIEW ONLY when checks were inspected but runtime verification was not performed or authorized.]
[Summary and any conditions]
```

When the user asked for review or quality checks, **present Findings first**, ordered by severity (Critical → High → Medium → Low), then the rest of the report.

## Handoff

- **PASS:** Implementation/structure verified and context is updated or verified-current. A user-declined proposal may be reported as an explicit exception. Draft-awaiting-review or pending-approval permits an implementation result with those limits clearly reported; do not claim the context was reviewed. Authorized integration remains explicitly user-controlled.
- **FAIL:** "Quality gate failed. [blockers]. Fix and re-run."

**Do not** commit, push, or deploy. Leave that to the user.
