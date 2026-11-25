# Behavioral verification contract

Read when planning, implementing, testing or verifying development work. This contract owns testing authority, test selection and realistic evidence; stage skills reference it rather than redefining those defaults. User and host instructions take precedence.

## Authority and proportionality

An implementation or bug-fix request includes focused local verification and useful regression-test changes within the affected behavior. Do not require a separate testing request. A verification-only request permits relevant existing checks; a review-only request remains inspect-and-report unless execution is also requested. Neither mode grants remediation authority. Delegated workers inherit the same mode, paths and explicit limits.

Respect explicit instructions such as no tests, no execution, restricted paths or local-only work; report the resulting evidence limits without repeatedly asking for the same permission. Ordinary verification does not authorize new tooling/dependency installs, paid or live external services, destructive data operations, unbounded suites, or unrelated refactors. Use existing project runners and deterministic local fixtures; ask only when a necessary check crosses a separate boundary.

Scale effort to uncertainty and impact. Reuse suitable existing coverage. Do not add tests for reversible low-impact edits with no meaningful behavior risk, duplicate coverage to increase counts, or create a test that merely restates the implementation. Explain a material verification limit instead of inventing busywork.

## What a useful test proves

Tests exist to establish that required functionality works, including meaningful edge cases and failure paths. They do not conserve the current code structure or bless whatever the implementation happens to return.

Derive expected results independently from requirements, confirmed domain rules or a reproduced defect. Use concrete expected values and observable outcomes. A test should remain valid when internals are rewritten while the behavior contract stays the same. Internal call order, private attributes and incidental snapshots are not contracts unless the requirement makes them observable obligations.

Choose edge cases from the changed behavior: empty input, boundary values, duplicates, invalid input, partial failure, retry/cancellation and state transitions as relevant. Do not mechanically add every category. Check important invariants as well as outputs, such as preserving survivor order, rejecting invalid input before mutation, or retaining saved data after restart.

For missing behavior coverage, follow red-green-refactor: observe the test fail for the intended reason, implement, then verify the outcome. Reuse an existing test that already demonstrates the defect. Preserve inherited and approved implementation; retrospective regression verification uses an isolated before-fix fixture and is reported honestly. Tests and expectations can also be wrong: investigate a failure against the contract before changing code or assertions. Do not weaken expectations merely to obtain green output.

## Select the smallest convincing proof

Identify the requirement and the failure a unit test cannot catch before choosing the check. Use real deterministic components when cheap and relevant. Mock genuinely remote, expensive, nondeterministic or unsafe dependencies, not the behavior the claim depends on. An in-memory fake does not prove a real storage adapter works.

| Changed behavior/risk | Suitable evidence |
|---|---|
| Pure calculation/validation | Concrete input/output and meaningful edge cases through its public interface |
| Files, database adapter or durable state | Temporary real storage; read back through a fresh instance/process when persistence is the claim |
| API/serialization boundary | Real local request/response or producer-consumer contract check, including rejection/error behavior |
| UI action/navigation/layout | Actual relevant interaction or render check using available tools; exercise the result and a relevant error/empty state, not only the handler |
| Async/lifecycle/retry | Controlled state transitions and adverse ordering/cancellation when relevant; condition-based waiting instead of arbitrary sleeps |

These are selections, not a mandatory suite. A small task may need one focused check. A risky boundary may need unit and integration evidence. A build proves compilation, not that an interaction works; a handler test does not prove a click reaches it. If UI or live-system execution is unavailable, state that limitation and the concrete user check still needed. Do not install a new framework solely to satisfy this table.

## Evidence

Map each material acceptance criterion to its check and actual result or limitation. Record the command, relevant input/version and environment. Reuse current evidence for unchanged relevant inputs and rerun after meaningful changes or uncertain freshness. Independently inspect delegated work and its results; an agent success summary alone is insufficient. Do not report broader success than the checks establish.
