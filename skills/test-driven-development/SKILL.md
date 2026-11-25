---
name: wa-test-driven-development
description: Use when a feature or bugfix needs missing behavior or regression coverage. Define requirements-derived expectations and meaningful edge cases, observe the intended failure, implement, then verify. Reuse suitable existing coverage and respect explicit user limits.
---

# Test-Driven Development (TDD)

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

## Overview

Read [references/behavioral-verification.md](references/behavioral-verification.md) first. It owns testing authority, proportionality, useful behavior/edge-case coverage and realistic evidence. An implementation request includes focused local verification. Explicit no-test/no-execution instructions, review-only scope and preservation of inherited work remain binding.

Use this procedure when a useful behavior or regression test is missing. Reuse suitable existing coverage for behavior-preserving refactors; do not add a test per function, duplicate coverage, or freeze internal implementation details. Test-first order is a technique for establishing evidence, not proof by itself that assertions or mocks are meaningful.

## Test-first rule

For new authorized behavior coverage, define the required outcome independently, observe the test fail for the intended reason, implement, then verify it passes. When implementation already exists, preserve it and reproduce the before-fix failure in a safe fixture/copy if available. Report retrospective regression verification honestly; never delete or reset inherited/approved work to manufacture test-first history.

## RED — Define and demonstrate the missing behavior

1. Identify the public behavior, requirement or reproduced defect. State concrete expected results and the relevant edge case/invariant; do not infer the expectation merely from today's implementation.
2. Reuse a suitable existing test, or write the smallest useful new test. It should remain valid when internals change while the contract stays the same.
3. Select the appropriate boundary using the shared verification contract. A pure calculation can use unit checks; persistence, request wiring or UI interaction may need a real local boundary.
4. Run the selected check with the actual project runner and inspect its failure. Confirm it fails because the behavior is missing/wrong, not an unrelated setup error. Record the command/result.

A test that already passes may be useful existing coverage. Do not corrupt a correct expectation to force a red result. For a claimed regression, use an isolated before-fix reproduction when possible; otherwise state that red was not established and limit the claim.

Example for a requirement that rejects blank email input:

```typescript
test('rejects blank email', async () => {
  const result = await submitForm({ email: '   ' });
  expect(result.error).toBe('Email required');
});
```

The error text is appropriate here only if it is part of the confirmed public contract. Avoid assertions on a private validator call or helper name. Choose other relevant cases such as a valid email or a missing value from the actual requirement, not a generic checklist.

## GREEN — Implement and verify the required outcome

1. Implement the smallest maintainable change that satisfies the behavior and existing architecture. Do not add unrelated features/refactors.
2. Run the selected tests/checks and relevant existing coverage of affected consumers/contracts. Read complete results and exit codes; avoid broadening to an unbounded suite without reason.
3. Investigate failures against the contract. Fix incorrect production behavior; correct a genuinely wrong expectation or fixture with an explicit reason. Never weaken a valid assertion just to obtain green output.
4. Confirm the proof covers the claim. A mocked `save()` call does not prove durable storage; a build or handler test does not prove a click reaches the handler.

For the example above, a public input validation change can make the test pass. If input is handled through an API, a focused local request check may also be needed to prove that the real request path applies that validation.

## REFACTOR — Preserve behavior while improving internals

After the relevant checks pass, remove duplication or improve boundaries within scope. Rerun affected checks after meaningful changes. Public behavior tests should survive internal renames, file moves and different algorithms without rewriting assertions. Do not retain an obsolete internal structure solely to satisfy a test; assess whether the assertion belongs to the required contract.

## Existing work and explicit limits

- Preserve inherited, user-authored and already approved changes. A safe before-fix copy can supply regression evidence; absence of one is a reported limit, not permission to reset work.
- Reuse current evidence for unchanged relevant inputs as defined by `wa-verification-before-completion`; a new message alone does not invalidate it.
- Honor explicit test/execution restrictions and review-only boundaries. State what is inspected and unverified; do not repeatedly ask to override a settled limit or pretend TDD was performed.
- For low-impact edits or sufficient existing coverage, select proportionate checks rather than adding ceremonial tests.
- For missing tooling or live/external systems, use permitted deterministic local evidence or report the gap. Do not install tools/contact services solely because this skill is loaded.

## Test-quality checks

Before reporting the scoped result:

- [ ] Expected outcomes trace to requirements or a demonstrated defect, not current code shape.
- [ ] Meaningful edge cases/invariants of the changed functionality are covered or their gaps disclosed.
- [ ] New regression evidence demonstrates the original failure when feasible; actual test order is reported honestly.
- [ ] Relevant checks ran with actual results, or explicit restrictions/unavailable checks are stated.
- [ ] Real boundaries were exercised when isolated units could not establish the claimed outcome.
- [ ] Existing work is preserved, and tests remain useful across internal refactors.
- [ ] Evidence identifies the checked inputs/environment and supports only the stated scope.

When adding mocks or test utilities, read `~/.wonsky-agents/skills/testing-anti-patterns/SKILL.md`. Unknown-cause defects go through `wa-systematic-debugging` before implementing a fix. Use `wa-verification-before-completion` before success claims.
