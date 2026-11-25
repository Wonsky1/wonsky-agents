# Development intake routing

This is the authoritative intake table for wa-using-dev-pipeline, wa-unified-dev-pipeline and its Python specialization. Entry points and validation scenarios refer here rather than maintaining another routing table. The selected skill owns its procedure; this reference selects the route.

## Resolve the target

Use the intended repository and task target. Python delivery uses `wa-dev-pipeline`; other languages or unresolved/mixed-language work use `wa-unified-dev-pipeline`, with the actual toolchain resolved per affected target. Debugging and other specialist routes retain that selection when returning to implementation. Do not turn an unknown language into Python by default.

## Select the route

| Request | First route |
|---|---|
| Unknown-cause bug, failure, regression or unexpected behavior | `wa-systematic-debugging`, then the target's pipeline at implementation or architecture as warranted |
| Verified root cause and clear local fix | Implementation through the target's pipeline |
| Clear, reversible, low-risk feature/change | Short workflow below |
| Ambiguous feature or user experience | `wa-brainstorming`, then the target's pipeline when the design is settled |
| Significant new feature, refactor or uncertain scope | Target's pipeline, strategic planning first |
| Architecture/pattern question with clear goals | `wa-solution-architect` |
| Approved design needing a breakdown | `wa-task-decomposer` or `wa-writing-plans`; reuse the accepted design |
| Approved implementation plan | `wa-executing-plans` or `wa-subagent-driven-development`; reuse the plan |
| Independent work streams | `wa-dispatching-parallel-agents` when scopes are independent; otherwise sequence |
| Review implementation/branch | `wa-requesting-code-review` with the actual diff and requirements |
| Harsh maintainability review | `wa-strict-code-quality-review` |
| GitHub PR review | `wa-pr-review-orchestrator`; analysis-only ends in chat; publishing has its own approval gate |
| Received review feedback | `wa-receiving-code-review` |
| Testing, quality or audit only | `wa-quality-gate` in the requested mode |
| Completion check | `wa-verification-before-completion` |
| Requested integration/cleanup after verification | `wa-finishing-a-development-branch` |
| Changelog/version work | `wa-changelog-versioning` |
| Work report/status summary | `wa-git-report` |
| Prompt/agent instruction authoring | `wa-prompt-engineering`; use `wa-writing-skills` for skill changes |
| Software request with no better specialist match | Target's pipeline |

## Platform modifiers for every route

These reads apply during debugging and review as well as design/implementation. Before analyzing a UI interaction/layout issue, read `~/.wonsky-agents/skills/ui-ux-pro-max/SKILL.md`. For SwiftUI, also read `~/.wonsky-agents/skills/swiftui-expert-skill/SKILL.md`; for macOS UI, also read `~/.wonsky-agents/skills/macos-design-guidelines/SKILL.md`. Load only their relevant references. Supply the same guidance to a delegated worker; a designer agent does not replace it. Reading guidance does not authorize commands, edits or UI access excluded by the user.

## Short workflow and escalation

Choose this route when the expected behavior is explicit, the affected boundary is understood, and the change is local, reversible and low risk. File count is evidence about size, not the risk decision.

State the scope and approach briefly, inspect relevant code/context, implement through `wa-implementation-guide`, run proportionate verification and review the scoped diff. Reuse clear end-to-end authority; no strategic plan, architecture proposal or additional confirmation is needed for a settled routine implementation. Preserve context/freshness, debugging, testing and instruction-change approval requirements.

Escalate to design/planning when uncertainty affects correctness, or the task changes authorization/security boundaries, destructive data operations, compatibility, shared contracts or coordinated services. A one-line permission change can warrant more scrutiny than six routine files. Ask only for the unresolved decision, batch related questions, and continue independent authorized work. An instruction/policy edit always retains its exact approval gate.

For substantial work, use the full pipeline and its meaningful review checkpoints. For small work, compress artifacts and review effort without removing correctness evidence.
