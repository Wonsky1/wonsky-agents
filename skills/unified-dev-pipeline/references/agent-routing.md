# Agent Routing Map

This file maps pipeline phases and routes to specialist sub-agents that may be available in the runtime (e.g. **Claude Code** with the **oh-my-claudecode** plugin). It is read by `unified-dev-pipeline` (and therefore by `dev-pipeline`).

## When to use this map

- **Agents available** (Claude Code + OMC, or any host exposing these agents): prefer the agent for the job, then return to the orchestrator to enforce gates.
- **No agents available** (plain Cursor, plain Codex): ignore this file. Use the skill fallbacks. The pipeline is fully functional without any agents.

**The orchestrator stays in control.** Agents execute a phase; they do not own the workflow. After an agent returns, you still enforce the approval gate, carry artifacts forward, and verify before claiming completion.

## Phase → agent map

| Pipeline phase / route | Preferred agent | What it does | Skill fallback |
|------------------------|-----------------|--------------|----------------|
| **Phase 1 — Strategy** | `oh-my-claudecode:analyst` (requirements, Opus), `oh-my-claudecode:planner` (interview + plan, Opus) | Crystallize scope, risks, acceptance criteria | `strategic-planner`, `brainstorming` |
| **Phase 2 — Architecture** | `oh-my-claudecode:architect` (read-only, Opus) | Reuse scan, pattern selection, design trade-offs | `solution-architect` |
| **Phase 3 — Decomposition** | `oh-my-claudecode:planner` | Order work into atomic tasks | `task-decomposer`, `writing-plans` |
| **Phase 4 — Implementation** | `oh-my-claudecode:executor` (Sonnet) | Focused task execution | `implementation-guide`, `executing-plans`, `subagent-driven-development` |
| **Parallel execution** | `ultrawork` skill / `team` | High-throughput independent work | `dispatching-parallel-agents` |
| **Debugging** | `oh-my-claudecode:tracer` (competing hypotheses), `oh-my-claudecode:debugger` (stack traces, build errors) | Evidence-driven root cause | `systematic-debugging`, `root-cause-tracing` |
| **Code review (own work)** | `oh-my-claudecode:code-reviewer` (severity-rated), `oh-my-claudecode:critic` (plans + code, Opus) | Find defects before merge | `requesting-code-review` |
| **Strict / "thermo-nuclear" review** | `oh-my-claudecode:critic`, `oh-my-claudecode:code-reviewer` | Harsh maintainability/abstraction/large-file bar | `strict-code-quality-review` |
| **GitHub PR review (others' PRs)** | `oh-my-claudecode:code-reviewer` for the analysis | 2-stage: strict diff review → post pending inline comments | `pr-review-orchestrator` → `github-pr-review` |
| **Security** | `oh-my-claudecode:security-reviewer` (OWASP) | Vulnerability + secret detection | `quality-gate` (security section) |
| **Work report / changelog** | (inline) | Management summary from git history; changelog/version bump | `git-report`, `changelog-versioning` |
| **Testing** | `oh-my-claudecode:test-engineer` (strategy, e2e, flaky), `oh-my-claudecode:qa-tester` (tmux CLI) | Language-agnostic test coverage | `test-driven-development`, `testing-anti-patterns`, language test skill |
| **Cleanup** | `oh-my-claudecode:code-simplifier` | Post-implementation simplification | (inline) |
| **UI / UX** | `oh-my-claudecode:designer` (Sonnet) | Stunning interfaces | (inline) |
| **Completion verification** | `oh-my-claudecode:verifier` | Evidence-based completion checks | `verification-before-completion` |
| **Branch completion / git** | `oh-my-claudecode:git-master` | Atomic commits, rebase, history | `finishing-a-development-branch` |
| **Codebase exploration** | `Explore` / `oh-my-claudecode:explore` | Find files & patterns fast | (inline search) |
| **External docs** | `oh-my-claudecode:document-specialist` | Web + reference lookup | (inline / context7) |
| **Data analysis / research** | `oh-my-claudecode:scientist` | Data analysis execution | (inline) |
| **Documentation writing** | `oh-my-claudecode:writer` (Haiku) | README, API docs, comments | (inline) |

## OMC skills worth invoking (Claude Code only)

These are workflow skills, not agents — invoke when the situation fits:

- `ultrawork` — parallel execution engine (Parallelization Route).
- `ralph` / `ralplan` — autonomous completion loops, when the user wants full autonomy past the quality gate. The default pipeline stops at the gate by design; only enter these on explicit request.
- `trace` — orchestrated competing-hypothesis tracing (heavy debugging).
- `deep-interview` — Socratic requirements crystallization for genuinely ambiguous asks (augments Phase 1).
- `wiki` — persistent project knowledge base that compounds across sessions.

## Guardrails

- Delegating to an agent does **not** skip a gate. The orchestrator still presents output for approval.
- Never let an agent commit, push, or deploy. That remains the user's explicit decision.
- An agent's claim of "done/passing/fixed" is not evidence. Run the Completion Verification Route yourself.
- Match the agent to the job; do not fan out agents for a single tightly-coupled change.
