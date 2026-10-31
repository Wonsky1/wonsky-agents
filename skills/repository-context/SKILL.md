---
name: repository-context
description: Use before repository planning, implementation, debugging or review; when handing work to another agent; or when proposing changes to AGENTS.md, repository rules, context, domain glossaries or architecture decisions. Establish task scope, load relevant documentation, write useful factual context drafts for user review and obtain approval before changing existing instructions or policies.
---

# Repository Context

Establish scope and read the relevant repository guidance before engineering work. Keep lasting instructions small, context evidence-based, and policies user-approved. This is a shared procedure used by the development pipeline, not a replacement for the selected engineering skill.

## Read and establish scope

1. Identify the intended repository from the user, active workspace or approved plan. Resolve real paths, distinguish repository root from task targets, and clarify genuinely ambiguous repositories. Do not infer broad authority from the current working directory.
2. Respect runtime-supplied instructions and their precedence. Discover every applicable ancestor instruction file down to each task target, including intermediate directories. Account for host-specific instruction files/overrides; a helper's list is supplemental, not a replacement for the host's instruction set. Do not recursively read unrelated subtrees. For a new file, inspect its existing parent chain first.
3. Establish **task scope** (outcome), **write scope** (authorized code/config/test areas), and **read scope** (relevant evidence). A directory mentioned in a task is a target, not automatically a strict read restriction. Root guidance, relevant contracts and shared docs may be read within the authorized repository unless the user restricts reading. Outside-repository access and explicitly restricted paths need applicable authorization. Reading a dependency never grants write permission. Command targets and generated source/guidance edits obey the same boundaries; authorized build/test outputs do not grant wider source-edit permissions. Do not broaden the task, write scope or an explicit read restriction without approval.
4. Read the repository's declared context index. Default, if present: `docs/agent-context/index.md`. Use existing README, CLAUDE.md, applicable `.cursor/rules`, CONTEXT-MAP.md, CONTEXT.md and ADRs where relevant. An absent index does not block independent code work. Record the gap and create useful factual context as a reviewable draft under the workflow below; do not silently treat absence as completion. Existing repository restrictions still govern writes. Reuse an existing equivalent context map rather than creating a competing one.
5. Select documents by **task meaning and affected paths**, including relevant cross-component contracts. Read the index and only matching modules/dependencies. Follow required links once, deduplicate and stop cycles. A broken required link or conflicting rule is a reported gap, not permission to invent its contents. Resolve uncertainty through scoped evidence; ask only when it blocks the work.
6. Distinguish **discovered**, **read**, and **applicable**. Existence, metadata, or a digest does not prove contents were read. Record actual document reads and the rules that govern the task. Never promote an observed pattern, historical ADR or an unapproved draft into a new policy. User/system/runtime authority still takes precedence.

Use the read-only helper in [scripts/context_tools.py](scripts/context_tools.py) when useful:

```sh
python3 <skill-directory>/scripts/context_tools.py discover <existing-task-path>
python3 <skill-directory>/scripts/context_tools.py check-links <index-or-module.md> --repo-root <root>
python3 <skill-directory>/scripts/context_tools.py fingerprint <explicitly-selected-document> ...
```

Resolve the script from this loaded skill directory. For non-Git trees use `discover PATH --repo-root ROOT`. `--global-instruction PATH` includes only explicitly supplied host instruction paths. Discovery returns candidate paths, never claims they were read. Link checks inspect the given file only, do not follow remote URLs, and do not validate anchors. Fingerprinting reads only the explicit file arguments. If discovery fails, report the failure and use only already-confirmed scope; never guess a different repository or broaden access. These helpers do not enforce filesystem permissions. For helper maintenance, run `python3 -B -m unittest discover -s <skill-directory>/scripts/tests -v`; tests use temporary repositories only.

## Write context, then ask for review

Repository engineering work includes maintaining useful repository context. Create missing factual context at its intended repository paths and update existing descriptive context with a reviewable diff. Do this before the final review request so the user can inspect and edit real files. Read existing text first, preserve accurate content and user-authored rules, and follow any stronger repository write restriction. Do not move, remove or replace existing guidance merely to fit a template.

Use a thin root entry point, an index and cohesive topic documents or the repository's established equivalent. Put confirmed responsibilities, requirements, behavior, boundaries, patterns, integration contracts, reasons and useful commands in the matching topic. Capture the useful evidence discovered during the task; do not omit it to meet a word or paragraph limit. Link existing sources rather than repeat them. A task plan, test log or chat summary is not repository context.

New context and factual updates awaiting review must be visibly marked **Draft — awaiting user review**. Separate confirmed facts from open questions. Label any proposed policy explicitly as **Proposed policy — not active**. New draft AGENTS.md files contain only a neutral context link and this review status; active repository-wide rules require approval. If AGENTS.md already exists, preserve it and propose the exact index-link addition when needed. Do not label an existing approved document wholly unapproved; identify the specific draft additions/changes in the diff or a clearly marked draft section. Agents may use independently verified facts as evidence, but must not treat draft prose as instruction authority.

After writing, inspect the diff and local links. Present the actual created/changed paths and reviewable content, explain the confirmed evidence and any policy proposal, then explicitly ask the user whether the context is correct and complete. Keep the review pending until the user answers. Apply requested corrections; approval of the concrete draft authorizes removing its draft markers. Reuse an unchanged exact approval rather than asking again. Rejection does not erase independent implementation work; agree on which draft content to remove or retain.

### Existing instructions and policies require exact approval before edits

Before adding or changing active instructions, user-authored rules, host adapters, established glossary definitions, historical ADR decisions, or skill instructions:

1. Check usefulness, evidence, scope and existing coverage. Distinguish descriptive facts, prescriptive rules and historical decisions.
2. Present one exact change package: operation/path, complete proposed text or diff including removals, reason/evidence, applicability and affected links. Batch related changes.
3. Ask for approval and wait. A direct instruction to persist specific content or approval of the already presented exact package is sufficient; ordinary implementation authority is not approval of an unspecified rule change.
4. Apply only the approved package. If its content, destination or base changes materially, present the revision. Inspect the final diff and local links. Report pending or declined items separately; do not use them as policy.

Factual draft creation above is the explicit exception to the pre-write approval gate; it never permits silently replacing user rules, inventing conventions, deleting guidance or writing into an unrelated repository. If applicable repository instructions require approval even for drafts, obey them and present the exact draft first. For adoption or modularization, read [references/templates.md](references/templates.md). Installation does not bootstrap another repository's context or rewrite its AGENTS.md.

## Handoff and freshness

Use an in-session packet; no new state file is required. Carry:
- Repository root, task outcome, read/write boundaries, explicit exclusions and their authorization.
- Applicable instruction paths and selected context paths, with read status and digests/version evidence when available.
- Governing constraints, known conflicts/missing docs, approved plan identity.
- Context drafts: paths, exact current diff, evidence and review status. Instruction/policy proposals: pending/approved/rejected, exact approved content and the user's authorizing message.

A fresh agent must read the applicable instructions and selected docs, or receive their complete current contents as trusted task context; a list of paths or a prior agent's summary is not a read. At handoff/resume, scope expansion, a context edit or evidence of external changes, check freshness and reread changed relevant documents. Recompute the instruction chain for newly affected paths. If a proposal's base changed, invalidate its applicability until reviewed. Do not reload unchanged documents on every command. A handoff grants no additional permissions.

## Required context outcome

Every repository engineering delivery reports a context outcome, including small fixes, delegated work and execution of an existing plan. At intake, name the entry guidance, context map and topics actually read. Missing coverage requires useful factual drafts; existing accurate coverage needs no cosmetic update. Do not generate context for unrelated repositories or fabricate lessons to satisfy the process.

Before completion, report the applicable outcome with paths and evidence:

- **updated**: the user reviewed the concrete context, requested corrections were applied, draft markers were resolved, and the resulting diff/links were inspected.
- **verified-current**: the relevant existing documents were read, cover the delivered behavior, and no useful confirmed knowledge is missing. Explain briefly why no edit is needed.
- **draft-awaiting-review**: actual factual context files or changes were written, inspected and presented; explicitly ask the user to review correctness and completeness. Implementation may be complete while context review remains pending.
- **pending-approval**: an existing instruction, proposed policy or stronger repository restriction needs exact approval before the requested write. Present that package; distinguish it from factual drafts already written.
- **declined**: the user rejected or deferred the context/decision; report the choice and preserve existing approved guidance. Do not reopen without new evidence or a request.

Carry the outcome in chat/handoffs, not an activity log. Do not claim a draft is reviewed because implementation was approved. Read-only reviews in repositories outside the authorized write scope report the documentation gap without creating files there.

### Content standard

Root AGENTS.md holds only critical repository-wide instructions and links. Topic documents contain all useful confirmed knowledge needed for future work, organized into focused paragraphs or sections. There is no fixed word, paragraph or file-count limit. Keep each statement concise and consequential; split unrelated topics and preserve discoverability through the index. Exclude repetition, speculative policy presented as fact, task diaries, transcripts, exhaustive inventories, generic coding tutorials and narration already obvious from code. The user should review a complete useful draft, not reconstruct omitted context from memory.
