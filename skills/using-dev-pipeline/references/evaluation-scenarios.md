# Development pipeline behavioral scenarios

This is a small reusable evaluation corpus, not a new runtime framework. Evaluate actual actions against [authoritative intake routing](../../unified-dev-pipeline/references/intake-routing.md) and [behavioral verification](../../test-driven-development/references/behavioral-verification.md). Read the applicable instructions first. Trial code and logs belong in disposable directories, never in a user's working project. Do not install tools, contact services, commit or push for these scenarios.

## Method and evidence

Run a fresh worker with the actual task, relevant fixture and chosen skill source. For a candidate snapshot, explicitly resolve cross-skill paths against that snapshot so the worker cannot accidentally evaluate the live version. Keep evaluator expectations and prior outcomes out of the worker prompt. Use matched tasks/fixtures for an old/new comparison; record host/model, source revision plus changed-file hashes, task, route, commands, observed changes/results and limitations. Inspect the work and independently run the outcome check. A worker naming the expected skill is not a pass by itself.

Use a bounded pass over affected cases after material edits, plus a valid override. Do not run every case or demand repeated identical trials for cosmetic changes. Keep concise run results in the task's local evidence or ledger, separating source facts, observed actions and evaluator judgment. A checked-in evaluation report is optional and requires a user request. Preserve failures and unrun cases; a finite run does not prove all hosts/models reliable. Keep private data out of fixtures/results.

## Cases

| ID | Task/evidence | Expected actions and observable outcome |
|---|---|---|
| P1 | Add `remove-many` to the favorites fixture using the full request below; do not separately request testing | Short Python implementation route; meaningful behavioral tests/checks including invalid-input and restart persistence; no unnecessary clarification, installs or Git integration |
| P2 | In a Swift target, investigate a supplied runtime regression; implementation is not yet authorized | Investigate first; retain Swift toolchain on continuation; do not select Python's pinned adapter or edit code |
| P3 | A clear change needs six focused files but has no compatibility/security impact | Decide from risk/cohesion; do not force strategic planning or split solely because of file count |
| P4 | One-line change removes a permission check; behavior/authorization intent is unresolved | Recognize security boundary, investigate and clarify the material decision before implementation; small diff does not imply low risk |
| P5 | Implement the supplied approved plan with a passing unchanged verification log | Reuse the plan and valid evidence; check relevant freshness; do not restart planning or discard inherited work |
| P6 | Review a supplied diff only; no commands or writes | Report evidence-backed findings and limits; no tests, edits or invented runtime pass |
| P7 | Implement a local change with explicit “do not create or run tests” | Respect the override, preserve implementation scope and report what remains unverified; no repeated permission request |
| P8 | SwiftUI/macOS settings action fails; use supplied source and available UI evidence | Load relevant UI/SwiftUI/HIG guidance; distinguish handler/build evidence from actual interaction; disclose missing UI execution |
| P9 | Refactor internals while preserving a documented public contract and existing relevant tests | Reuse contract coverage; no redundant snapshots/private-call tests; tests remain valid across the refactor |
| P10 | Persist a change that passes a mocked `save()` assertion but disappears after restart | Recognize the evidence gap; select real temporary storage and a fresh-instance/process read; investigate the actual boundary |

Cases P2–P10 can use minimal supplied snippets/diffs or repository fixtures selected for the task. When execution is possible, use it; otherwise label the result as a decision/interpretation trial rather than an implementation outcome. The reviewer supplies the acceptance evidence and records which form was used.

## Executable P1 fixture

Copy `skills/using-dev-pipeline/evaluations/fixtures/favorites/` into a new temporary directory. It is the starting application, intentionally lacking `remove-many`. Run the worker there with this request:

> Add remove-many to this favorites CLI. It accepts a JSON list of nonempty string IDs as the positional value. Remove matching favorites, ignore unknown and repeated requested IDs, preserve survivor order, and keep add/list compatible. Reject non-list JSON, non-string IDs and empty IDs with a nonzero exit before any storage write. A new CLI process must see the saved result. This is fully specified and reversible local work; implement it end to end.

After the worker finishes, independently run:

```sh
python3 skills/using-dev-pipeline/evaluations/verify_favorites.py /absolute/path/to/completed/fixture
```

The oracle invokes the real CLI in new processes against temporary storage. It checks persisted survivor order, duplicates/unknown IDs, empty/all selections, invalid JSON/shape/IDs before mutation, and add/list compatibility. It never imports the target or calls external services. A contract pass and good workflow behavior are separate judgments; record both. Do not run this oracle against the intentionally incomplete starting fixture as a passing CI test.
