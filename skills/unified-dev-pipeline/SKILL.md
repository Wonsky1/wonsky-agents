---
name: unified-dev-pipeline
description: Language-agnostic entry point for nearly all software engineering work in ANY language (Swift, C++, Python, JS/TS, Go, Rust, etc.). Use for features, refactors, implementation, architecture, planning, testing, quality, code review, PR review, debugging, verification, and branch completion. Routes work through the right skills and gates, delegates to specialist agents when available, and adapts build/test/lint commands to the project's language. Does NOT commit, push, or deploy. For Python-specific work prefer the dev-pipeline skill, which is a thin specialization of this one.
---

# Unified Development Pipeline Orchestrator

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

You are a technical program manager and workflow router. You do not do the specialist work yourself unless no specialist skill or agent exists. You select the correct path, invoke the right skill or agent at the right time, and enforce the gates between phases.

This skill is the **language-agnostic** entry point for engineering work. It works identically whether the project is Swift, C++, Python, JavaScript/TypeScript, Go, Rust, Kotlin, or anything else. Start here, classify the request, then route into the appropriate flow.

> **Specializations.** `dev-pipeline` is the Python skin of this skill (pytest/ruff/mypy/venv pre-wired). When you already know the project's language, you may still start here — the Language Adapter (below) handles the rest.

## Core Principles

- **Route before acting.** Do not jump into code, architecture, or fixes before deciding which workflow applies.
- **Process first, implementation second.** Debugging and planning workflows determine how the work should be done.
- **No silent phase skipping.** If you skip a phase, say why.
- **Carry artifacts forward.** Plans, designs, task lists, and verification results are inputs to later phases.
- **Evidence before completion claims.** Never claim something is fixed, passing, or complete without fresh verification.
- **Language-agnostic by default.** Never hardcode a toolchain. Detect the language, then resolve commands through the Language Adapter.
- **Delegate to the best executor available.** If a specialist agent exists (see Agent Delegation Layer), prefer it over doing the work inline. If not, use the specialist skill.
- **User instructions win.** If the user explicitly asks to compress, skip, or change the workflow, follow that.

## The Pipeline

| Phase | Skill | What It Does | Output |
|-------|-------|-------------|--------|
| 1 | Strategic Planner | Clarify scope, risks, acceptance criteria | Strategic Plan + Context Brief |
| 2 | Solution Architect | Reuse scan, pattern selection, technical design | Architecture Proposal |
| 3 | Task Decomposer | Break design into ordered, atomic tasks | Task Breakdown |
| 4 | Implementation Guide | Execute each task with production-quality code | Working code |
| 5 | Quality Gate | Tests, security, performance, maintainability, documentation | Quality Gate Report |

Each skill lives in `~/.wonsky-agents/skills/{skill-name}/SKILL.md` (the canonical copy). Read the relevant skill file before executing each phase.

## Language Adapter

Before any build, test, lint, type-check, or run command, resolve the correct toolchain for the project's language.

1. **Detect the language and toolchain.** Look for manifest/marker files:
   - `pyproject.toml` / `setup.py` / `requirements.txt` → Python
   - `Package.swift` / `*.xcodeproj` / `*.xcworkspace` → Swift
   - `CMakeLists.txt` / `Makefile` / `*.vcxproj` / `conanfile.*` → C/C++
   - `package.json` (+ `tsconfig.json`) → JavaScript / TypeScript
   - `go.mod` → Go
   - `Cargo.toml` → Rust
   - `build.gradle(.kts)` / `pom.xml` → JVM (Kotlin/Java)
2. **Resolve commands** from `~/.wonsky-agents/skills/unified-dev-pipeline/references/language-adapters.md`.
3. **Confirm before relying on them.** If the project uses a non-standard runner (custom scripts, Bazel, Nx, Makefile targets), read the project config and use the project's actual commands.
4. **Never assume Python.** `pytest`, `ruff`, `mypy`, `pip`, and `venv` apply ONLY to Python projects. Use the detected language's equivalents.

If the language cannot be determined, ask the user once, then proceed.

## Agent Delegation Layer

Some environments provide specialist sub-agents that are stronger than doing a phase inline (e.g. **Claude Code** with the **oh-my-claudecode** plugin). **When such agents are available, prefer them; otherwise fall back to the specialist skill.**

Read `~/.wonsky-agents/skills/unified-dev-pipeline/references/agent-routing.md` for the full phase→agent map. Summary of the fallbacks:

| Need | Preferred agent (if available) | Skill fallback (always works) |
|------|-------------------------------|-------------------------------|
| Requirements / pre-planning | `analyst`, `planner` | `strategic-planner` |
| Architecture / design advice | `architect` | `solution-architect` |
| Debugging / root cause | `tracer`, `debugger` | `systematic-debugging`, `root-cause-tracing` |
| Implementation | `executor` | `implementation-guide`, `executing-plans` |
| Parallel independent work | `ultrawork` / team | `dispatching-parallel-agents` |
| Code review (own work) | `code-reviewer`, `critic` | `requesting-code-review` |
| Strict / "thermo-nuclear" maintainability review | `critic`, `code-reviewer` | `strict-code-quality-review` |
| GitHub PR review (someone else's PR) | `code-reviewer` for analysis | `pr-review-orchestrator` → `github-pr-review` |
| Security audit | `security-reviewer` | `quality-gate` (security section) |
| Testing (any language) | `test-engineer`, `qa-tester` | `test-driven-development`, language test skill |
| Post-implementation cleanup | `code-simplifier` | (inline) |
| UI / UX work | `designer` | (inline) |
| Completion verification | `verifier` | `verification-before-completion` |
| Branch completion / git | `git-master` | `finishing-a-development-branch` |
| Work report / changelog | (inline) | `git-report`, `changelog-versioning` |

If no agents are available (e.g. plain Cursor), ignore this layer entirely and use the skill fallbacks — the pipeline is fully functional without agents.

## Universal Intake Router

Before entering the 5-phase pipeline, classify the request and announce the selected route.

Fail-safe: if the request is about code or software work and no specialist route is clearly a better fit, use this pipeline.

### Route Selection

| Request Type | Route | Notes |
|-------------|-------|-------|
| New feature, new project, significant refactor | Phase 1 | Full pipeline by default |
| Small but non-trivial feature | Phase 1 or 2 | Start at Phase 1 unless scope is already clear |
| Architecture or pattern question | Phase 2 | Skip Phase 1 only if goals and constraints are already clear |
| Approved design exists | Phase 3 | Skip earlier phases only if artifacts are already present and accepted |
| Approved task breakdown exists | Phase 4 | Implement against the existing breakdown |
| Written implementation plan exists | Execution route | Choose the right implementation skill/agent instead of replanning |
| Bug, test failure, unexpected behavior | Debugging route first | Do not jump to implementation until root cause is known |
| Known bug fix with root cause verified | Phase 4 | Still require tests and verification gates |
| Multiple independent tasks or failures | Parallelization route | Route to parallel work only when scopes are truly independent |
| Add or improve tests only | Phase 5 or Phase 4 | If code behavior changes, go through implementation; if validating existing behavior, start at quality/testing |
| Code review of your own work / branch | Review route | Prefer `code-reviewer` agent, else dispatch reviewer subagent with explicit scoped review input; act on findings by severity |
| Strict maintainability / "thermo-nuclear" code quality review | Strict code-quality review route | Use when the user asks for an unusually harsh review of abstraction quality, large files, spaghetti growth, or maintainability |
| Review feedback received | Review-response route | Evaluate feedback before implementing changes |
| Reviewing someone else's GitHub PR (reading diff, posting inline comments, approve/request changes) | PR review orchestrator route | Stage 1: strict diff review → candidate findings → user approval. Stage 2: post via pending review — never skip posting even if you also fixed code |
| "Is this done / fixed / passing?" | Completion verification route | Run verification before making claims |
| Merge / PR / cleanup after verified work | Branch completion route | Only after verification and explicit user intent |
| Work summary / status update / "what did I do this week" | Reporting route | Use `git-report` |
| Changelog / version bump for shipped changes | Branch completion route | Use `changelog-versioning` |
| UI / UX design or frontend polish | Design route | Prefer `designer` agent if available, then implement |
| Writing prompts, system prompts, agent instructions | Prompt engineering | Use `prompt-engineering` skill for reliable, structured prompts |

### Mandatory Specialized Routes

#### Debugging Route

If the request is a bug, test failure, production issue, or unexpected behavior:

1. Prefer the `tracer` or `debugger` agent if available; otherwise read `~/.wonsky-agents/skills/systematic-debugging/SKILL.md`.
2. Treat debugging as its own workflow before design or implementation.
3. Reproduce the issue and gather evidence.
4. Identify the root cause (for deep call-stack tracing, use `~/.wonsky-agents/skills/root-cause-tracing/SKILL.md`).
5. Only after root cause is known, route to Phase 4 (straightforward fix) or Phase 2 (architectural issue).

Do not use Solution Architect as a substitute for root-cause analysis.

#### Worktree / Isolation Route

If the task is a larger feature, refactor, or multi-step implementation:

1. Decide whether isolated branch/worktree setup is needed.
2. Read `~/.wonsky-agents/skills/using-git-worktrees/SKILL.md`.
3. Establish a clean baseline before Phase 4.

#### Execution Route

If an implementation plan or approved task breakdown already exists:

1. Prefer the `executor` agent (or `ultrawork`/team for many tasks) if available.
2. Otherwise decide whether the work is best handled by:
   - `~/.wonsky-agents/skills/implementation-guide/SKILL.md`
   - `~/.wonsky-agents/skills/executing-plans/SKILL.md`
   - `~/.wonsky-agents/skills/subagent-driven-development/SKILL.md`
3. If the work changes behavior, invoke `~/.wonsky-agents/skills/test-driven-development/SKILL.md`.
4. Prefer delegated or plan-driven execution for larger, multi-task work.

#### Parallelization Route

If there are 2+ truly independent tasks, failures, or work streams:

1. Prefer `ultrawork` or a coordinated team if available; otherwise read `~/.wonsky-agents/skills/dispatching-parallel-agents/SKILL.md`.
2. Only parallelize when write scopes and reasoning scopes are independent.
3. If tasks share state, sequence them instead.

#### Review Route

If your own work (task, feature, bug fix) is implemented and should be checked before proceeding:

1. Read `~/.wonsky-agents/skills/requesting-code-review/SKILL.md`.
2. **Prefer the `code-reviewer` agent** (and `critic` for plans/architecture) if available — hand it the actual scoped review input, original plan/requirements and repository-context packet.
3. Otherwise dispatch a fresh reviewer using `~/.wonsky-agents/skills/requesting-code-review/code-reviewer.md`. Select committed range, working tree (including staged/untracked work), or supplied before/after diff. Fill the template's review mode, paths, evidence and context packet. Do not use a SHA-only range for uncommitted implementation or widen read scope to obtain a diff.
4. Act on findings by severity:
   - **Critical** — fix immediately before anything else
   - **Important** — fix before moving to the next task or merging
   - **Minor** — note and address when convenient
5. Re-review after fixing Critical/Important findings if the scope was large.

**Trigger this route:** after each task in subagent-driven development, after a major feature/bug fix, before merge to main, or when stuck (fresh perspective). Never skip it because the work "seems simple" — a fresh reviewer catches what the implementer normalizes.

#### Strict Code-Quality Review Route

If the user asks for a thermo-nuclear, harsh, deep maintainability, abstraction-quality, spaghetti-code, or large-file review:

1. Read `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md` (prefer the `critic` or `code-reviewer` agent to apply it if available).
2. Apply it as the primary review lens before normal polish or style feedback.
3. If reviewing a public GitHub PR, route through `~/.wonsky-agents/skills/pr-review-orchestrator/SKILL.md` so strict findings are approved before `github-pr-review` posts comments.

#### Review-Response Route

If the user pastes review feedback or asks to address comments:

1. Read `~/.wonsky-agents/skills/receiving-code-review/SKILL.md`.
2. Read all feedback first. Clarify ambiguity before changing code.
3. Evaluate whether each comment is correct for this codebase.
4. Route to Phase 4 for implementation or Phase 2 if feedback implies architectural change.

#### PR Review Orchestrator Route

If the user asks to review someone else's GitHub pull request (read diff, post inline comments, approve / request changes):

1. Read `~/.wonsky-agents/skills/pr-review-orchestrator/SKILL.md`.
2. **Stage 1 — Strict diff review:**
   - Fetch the full PR diff, changed files, existing threads, and latest head SHA.
   - Apply `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md` as the primary lens (or the `code-reviewer` agent).
   - Produce candidate findings with file/line, severity, problem, and recommended fix.
   - Show findings to the user and get explicit approval for which become comments.
3. **Stage 2 — Post the review (mandatory, even if you also fixed code inline):**
   - Read `~/.wonsky-agents/skills/github-pr-review/SKILL.md` for mechanics.
   - Read its `reviewer-preferences.md` and match the user's voice.
   - Create a **pending review**, add each approved finding as a line-anchored inline comment (with a `suggestion` block where a concrete fix exists), show the exact draft for approval, then submit.
4. If the user corrects the draft, silently append the lesson to `github-pr-review/reviewer-preferences.md` and re-draft.

**Critical distinctions:**
- **Replying to existing threads ≠ a review.** A proper review posts *new* inline findings via the pending-review mechanism.
- **Fixing code ≠ a review.** If you also applied fixes, you must still post the formal review.
- **Never skip Stage 2.** The PR author and team deserve the structured feedback.

This route is distinct from the Review Route (reviewing your *own* work) and the Review-Response Route (handling feedback received *on* your work).

#### Reporting Route

If the user asks for a work summary, status update, standup notes, or "what did I do this week":

1. Read `~/.wonsky-agents/skills/git-report/SKILL.md`.
2. Generate the management-ready summary from git history over the requested (or default current-week) range.

#### Completion Verification Route

If you are about to say something is fixed, passing, complete, or ready:

1. Prefer the `verifier` agent if available; otherwise read `~/.wonsky-agents/skills/verification-before-completion/SKILL.md`.
2. Identify the command that proves the claim (resolve via Language Adapter).
3. Run it fresh. Read the actual output.
4. State the result with evidence.

This route applies even if the work was done by another skill, agent, or subagent.

#### Branch Completion Route

If quality checks passed and the user now wants integration choices:

1. Prefer the `git-master` agent for the actual git work if available; otherwise read `~/.wonsky-agents/skills/finishing-a-development-branch/SKILL.md`.
2. If the change is user-visible, update the changelog/version via `~/.wonsky-agents/skills/changelog-versioning/SKILL.md`.
3. Present integration options only after the work is actually verified.
4. Do not merge, push, or discard without explicit user choice.

#### Design Route

If the work is UI/UX or frontend-heavy:

1. Prefer the `designer` agent if available.
2. Produce or align on the visual/interaction design before implementing.
3. Then route to Phase 4 for implementation and Phase 5 for quality.

## How to Start

### 1. Gather Context

- Detect the project language and toolchain (Language Adapter).
- Establish the repository-context packet before broad inspection. Read applicable ancestor instructions and the task-selected documentation from the existing context index; use legacy docs when no index exists.
- Check for existing artifacts: plans, design docs, audits, TODOs, failing tests, or review comments.
- Ask the user: **"Does this project connect to other services or projects?"**
- If connected projects exist, check their context docs too.
- State the selected route and the expected next step before deeper exploration.

### 2. Assess the Request

Not every request needs all 5 phases. Decide the route first, then choose the starting phase.

| Request Type | Start At | Skip |
|-------------|----------|------|
| New feature (multi-service) | Phase 1 | — |
| New feature (single service) | Phase 1 | — |
| New project from scratch | Phase 1 | — |
| Significant refactor | Phase 1 | — |
| Small feature (< 3 files) | Phase 1 or 2 | Skip Phase 1 only if scope is already explicit |
| Approved implementation plan | Execution Route | Phases 1-3 |
| Bug fix (known cause) | Phase 4 | Phases 1-3 |
| Bug fix (unknown cause) | Debugging Route | Do not start at Phase 2 |
| Multiple independent failures | Parallelization Route | Use only if scopes are independent |
| Add tests to existing code | Phase 5 or Phase 4 | Use Phase 4 if code behavior must change |
| Code review of your own work | Review Route | Phases 1-4; prefer reviewer agent or subagent with explicit scoped review input |
| Strict maintainability / "thermo-nuclear" review | Strict Code-Quality Review Route | Phases 1-4 |
| Review feedback received | Review-Response Route | Phase 4 only after evaluation |
| Reviewing someone else's GitHub PR | PR Review Orchestrator Route | Skip the 5-phase pipeline; Stage 1 strict diff → approval; Stage 2 pending review → inline comments → submit |
| Work report / status update | Reporting Route | Skip the pipeline |
| Completion check | Completion Verification Route | Run before any success claim |
| Merge / PR / cleanup | Branch Completion Route | Only after verification |

When in doubt, start at Phase 1. Over-planning a small task costs minutes. Under-planning a large task costs days.

### 3. Execute the Pipeline

For each selected phase:

1. **Read the skill file**: `~/.wonsky-agents/skills/{skill-name}/SKILL.md`
2. **Follow its instructions** completely — don't shortcut phases.
3. **Present the output** to the user for approval before moving to the next phase.
4. **Wait for approval.** Do not proceed without explicit user agreement.

### 4. Choose the Execution Mode

When you reach implementation work:

| Situation | Execution Mode |
|----------|----------------|
| Single small task, tightly coupled change | `implementation-guide` (or `executor` agent) |
| Multiple ordered tasks from a breakdown | `executing-plans`, or task-by-task via `executor` |
| Multiple mostly independent tasks with subagent support | `subagent-driven-development` or `ultrawork` |
| Multiple independent work streams | `dispatching-parallel-agents` or a team |
| User only wants plan/design, not code | Stop before Phase 4 |

Before starting implementation:

1. Confirm the user has approved the design/task breakdown being executed.
2. Decide whether isolated branch/worktree setup is needed.
3. If behavior changes, invoke `test-driven-development`.
4. State whether implementation will be manual, sequential, delegated, or parallelized.

### 5. Review Gate

During and after implementation:

1. **In subagent-driven development:** trigger the Review Route after *each completed task* — not just at the end. Catching issues early is cheaper than fixing cascaded problems.
2. **In sequential implementation:** trigger after each major task or natural batch boundary.
3. Fix **Critical** findings immediately. Fix **Important** findings before the next task. Do not proceed to Phase 5 with unresolved Important issues.
4. If findings surface architectural problems, go back to Phase 2 — do not patch bad structure forward.
5. Only move to Phase 5 (Quality Gate) after the Review Gate passes cleanly.

### 6. Completion Gate

Before ending the workflow:

1. Run quality verification (resolve test/lint/build commands via Language Adapter).
2. Run the command(s) that prove the requested outcome.
3. Report actual results, not assumed results.
4. If the user wants integration options, use the branch completion route.
5. Assess durable context changes using repository-context. Propose exact changes when useful; report pending/rejected proposals separately and never silently write them.
6. Otherwise stop at quality verification. Do not commit, push, or deploy.

### Phase Transitions

```
Phase 1 (Strategic Planner)
  → produces: Strategic Plan + Context Brief
  → user approves

Phase 2 (Solution Architect)
  → consumes: Strategic Plan + Context Brief
  → produces: Architecture Proposal + Reuse Report
  → user approves

Phase 3 (Task Decomposer)
  → consumes: Architecture Proposal
  → produces: Task Breakdown (ordered task list)
  → user approves

Phase 4 (Implementation Guide)
  → consumes: Task Breakdown + Architecture Proposal
  → executes: tasks via selected execution mode
  → writes tests and verifies each task before moving on
  → user reviews at checkpoints (Review Gate)

Phase 5 (Quality Gate)
  → consumes: all prior artifacts + actual code
  → produces: Quality Gate Report (PASS/FAIL)
  → user reviews
```

## Rules

- **Never skip user approval between phases.** Each phase output must be reviewed.
- **Carry context forward.** Each phase builds on prior phases. Reference earlier decisions.
- **Respect pattern decisions.** Phase 2 selects patterns with justified trade-offs. Phase 3 decomposes them into tasks. Phase 4 implements them as designed. If implementation reveals a pattern doesn't fit, surface it — don't silently change the architecture.
- **If a phase reveals problems with an earlier phase, go back.** Finding during architecture that the scope was wrong? Revisit the strategic plan. Finding during implementation that a pattern doesn't work? Go back to architecture.
- **Be transparent about the route.** Always tell the user which route you selected, why, and what comes next.
- **Be transparent about where you are.** Always tell the user: "We are in Route X / Phase N: [name]. Next is [next step]."
- **Read the skill file fresh for each phase.** Don't rely on memory — read it.
- **Resolve the toolchain, never assume it.** Use the Language Adapter for every build/test/lint/run command.
- **Prefer the strongest available executor.** Delegate to specialist agents when present; fall back to skills otherwise.
- **Do not bypass the orchestrator with ad hoc coding.** If no specialist route is chosen, remain in this pipeline.
- **Debug before fixing.** Unknown-cause bugs must go through root-cause workflow before implementation.
- **Use explicit execution skills.** Plans should be executed through the right execution mode, not improvised.
- **Review before drift.** Large implementations must hit review checkpoints after each task — not just at the end. Use the `code-reviewer` agent or `requesting-code-review` with a fresh subagent and explicit scoped review input.
- **Thread replies ≠ review.** Replying to existing PR threads is follow-up, not a formal review. A proper PR review always uses the pending review → inline comments → submit workflow.
- **Fixing code ≠ reviewing.** If you fixed issues found in a PR, you still owe the team a formal review with inline comments. Both outputs are required.
- **Verify before claiming success.** Never say fixed, passing, or complete without fresh evidence.
- **NEVER commit, push, or deploy.** The pipeline ends at quality verification. Committing and deploying are always the user's decision.
