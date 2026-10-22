---
name: repository-context
description: Use before repository planning, implementation, debugging or review; when handing work to another agent; or when proposing changes to AGENTS.md, repository rules, context, domain glossaries or architecture decisions. Establish task scope, load relevant documentation and obtain approval before changing persistent guidance.
---

# Repository Context

Establish scope and read the relevant repository guidance before engineering work. Keep lasting instructions small, evidence-based and approved. This is a shared procedure used by the development pipeline, not a replacement for the selected engineering skill.

## Read and establish scope

1. Identify the intended repository from the user, active workspace or approved plan. Resolve real paths, distinguish repository root from task targets, and clarify genuinely ambiguous repositories. Do not infer broad authority from the current working directory.
2. Respect runtime-supplied instructions and their precedence. Discover every applicable ancestor instruction file down to each task target, including intermediate directories. Account for host-specific instruction files/overrides; a helper's list is supplemental, not a replacement for the host's instruction set. Do not recursively read unrelated subtrees. For a new file, inspect its existing parent chain first.
3. Establish **task scope** (outcome), **write scope** (authorized code/config/test areas), and **read scope** (relevant evidence). A directory mentioned in a task is a target, not automatically a strict read restriction. Root guidance, relevant contracts and shared docs may be read within the authorized repository unless the user restricts reading. Outside-repository access and explicitly restricted paths need applicable authorization. Reading a dependency never grants write permission. Command targets and generated source/guidance edits obey the same boundaries; authorized build/test outputs do not grant wider source-edit permissions. Do not broaden the task, write scope or an explicit read restriction without approval.
4. Read the repository's declared context index. Default, if present: `docs/agent-context/index.md`. Use existing README, CLAUDE.md, applicable `.cursor/rules`, CONTEXT-MAP.md, CONTEXT.md and ADRs where relevant. An absent index is not a blocker and does not authorize creating one. Do focused inspection; propose a minimal index when it would improve future work.
5. Select documents by **task meaning and affected paths**, including relevant cross-component contracts. Read the index and only matching modules/dependencies. Follow required links once, deduplicate and stop cycles. A broken required link or conflicting rule is a reported gap, not permission to invent its contents. Resolve uncertainty through scoped evidence; ask only when it blocks the work.
6. Distinguish **discovered**, **read**, and **applicable**. Existence, metadata, or a digest does not prove contents were read. Record actual document reads and the rules that govern the task. Never promote an observed pattern, historical ADR or an unapproved draft into a new policy. User/system/runtime authority still takes precedence.

Use the read-only helper in [scripts/context_tools.py](scripts/context_tools.py) when useful:

```sh
python3 <skill-directory>/scripts/context_tools.py discover <existing-task-path>
python3 <skill-directory>/scripts/context_tools.py check-links <index-or-module.md> --repo-root <root>
python3 <skill-directory>/scripts/context_tools.py fingerprint <explicitly-selected-document> ...
```

Resolve the script from this loaded skill directory. For non-Git trees use `discover PATH --repo-root ROOT`. `--global-instruction PATH` includes only explicitly supplied host instruction paths. Discovery returns candidate paths, never claims they were read. Link checks inspect the given file only, do not follow remote URLs, and do not validate anchors. Fingerprinting reads only the explicit file arguments. If discovery fails, report the failure and use only already-confirmed scope; never guess a different repository or broaden access. These helpers do not enforce filesystem permissions. For helper maintenance, run `python3 -B -m unittest discover -s <skill-directory>/scripts/tests -v`; tests use temporary repositories only.

## Persistent context changes require approval

This gate applies to creation, editing, removal, renaming, moving and generated rewrites of:
- Root or nested AGENTS.md, host rule files, CLAUDE.md and instruction adapters.
- The context index/modules, domain glossaries/maps, ADRs, and other docs used as lasting repository guidance, regardless of filename.

Ordinary implementation files, task-local notes and user-facing documentation follow the task's authorization. Calling a guidance file a README, draft, generated file or task note does not exempt it. Never stash unapproved guidance in the repository to bypass this gate.

Before a protected write:
1. Check whether it is durable and useful, confirmed by the user or evidence, scoped correctly, and absent from existing docs. Separate descriptive facts, prescriptive rules, how-to guidance and historical decisions. Prefer an existing document/link over duplicate text. Exclude task logs, guesses and generic coding advice.
2. Present one concrete change proposal in chat: exact path and operation, exact new text or diff (including removals), reason/evidence, applicability and affected links. Batch related changes. Do not create a repository proposal file unless that write is itself authorized.
3. Ask for approval of that proposal and wait. Agreement about a business fact, approval to implement code, or a general request to keep docs current does not approve an unspecified persistent change. A direct instruction to persist specific text, or approval of an already presented concrete change package, is authorization; do not ask again for the same action.
4. Apply only the approved content and operations. If the content or destination changes materially, or the underlying file changed since approval, show the revised proposal before writing. Rejection leaves files unchanged; do not propose the same rejected change repeatedly without new evidence or a user request.
5. Check the resulting diff and local links. State which approved changes were applied and which proposals are pending or rejected. Continue independent code work while waiting, but do not claim pending documentation is complete or use unapproved guidance as established policy. Ask before dependent work if the unresolved decision changes correctness.

For first adoption or modularization, read [references/templates.md](references/templates.md). Propose a short root AGENTS.md and only useful context modules. Preserve existing rules, locations and references during migration; never regenerate an existing file from a template. Each removal/move needs to appear in the proposal. Do not bootstrap other repositories as a side effect of installing this skill.

## Handoff and freshness

Use an in-session packet; no new state file is required. Carry:
- Repository root, task outcome, read/write boundaries, explicit exclusions and their authorization.
- Applicable instruction paths and selected context paths, with read status and digests/version evidence when available.
- Governing constraints, known conflicts/missing docs, approved plan identity.
- Protected-document proposals: pending/approved/rejected, exact approved content or diff and the user's authorizing message.

A fresh agent must read the applicable instructions and selected docs, or receive their complete current contents as trusted task context; a list of paths or a prior agent's summary is not a read. At handoff/resume, scope expansion, a context edit or evidence of external changes, check freshness and reread changed relevant documents. Recompute the instruction chain for newly affected paths. If a proposal's base changed, invalidate its applicability until reviewed. Do not reload unchanged documents on every command. A handoff grants no additional permissions.

## Completion check

Before finishing, assess whether the task revealed durable context worth proposing. If none, say nothing extra and create nothing. If needed, provide a compact proposal and report its approval status separately from implementation/test status. Missing optional context does not force creation or block otherwise authorized work.
