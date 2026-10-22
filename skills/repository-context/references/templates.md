# Repository context templates

Use only for an approved initial setup or an approved migration. Adapt to observed repository facts. Never install placeholders, invent conventions, or create every example module. Existing useful README, glossary and ADR files remain authoritative at their existing locations.

## Thin root AGENTS.md

Aim for roughly 30–60 lines, not a mandatory quota. Keep only repository-wide invariants, critical constraints, a context entry point and change authority. Move detailed conventions/examples to linked docs with approval. Generic SOLID tutorials and transient task notes do not belong here.

Example content to adapt and propose:

```markdown
# Repository instructions

- Before engineering work, read `docs/agent-context/index.md` and the documents applicable to the task and affected paths.
- Respect applicable nested instructions. Keep edits within the authorized task; reading shared context does not expand write scope.
- Before adding, modifying, moving or deleting persistent repository guidance, show the exact change and obtain user approval. Apply previously approved exact changes without asking again.
- If documentation conflicts with the task or code, surface the conflict; do not silently change the rule to match the implementation.

## Repository-wide constraints

Include only confirmed constraints that apply to every task. Omit this section if none exist.
```

The last example section is instructional scaffolding; replace or omit it in the proposal. Product instructions must stay repository-relative and portable: do not hardcode the owner's home directory or require a globally installed personal skill for other contributors. The personal dev pipeline supplies the reusable procedure; the project AGENTS.md keeps the minimal behavior explicit.

## Context index

Use one small Markdown table. Paths are relative to the index itself. Select on semantic relevance OR affected files, then follow any explicitly required dependencies; path matching alone is insufficient.

```markdown
# Context index

Read only matching documents and their required dependencies. The root instructions always apply. A link here does not grant permission to modify the linked document.

| Read when | Applies to | Document | Kind |
|---|---|---|---|
| Changing component boundaries or dependencies | Cross-component changes | [Architecture](architecture.md) | Rules and system facts |
| Implementing or verifying code | Development work | [Development](development.md) | How-to and conventions |
| Payment behavior, webhooks or API/storage contracts change | Billing and its callers | [Billing](areas/billing.md) | Domain invariants |
| Business terminology matters | Relevant domain | [Glossary](../../CONTEXT.md) | Approved definitions |
```

Include rows only for real documents. Do not create empty billing/frontend examples. For a small project the index can point exclusively to existing docs. Prefer 3–8 useful entries initially; this is a heuristic, not a limit. Link an ADR when its decision is relevant, not the entire ADR archive. Nested indexes are justified only when the main map becomes unwieldy.

## Context module

A module contains the minimum non-obvious information that changes future decisions:

```markdown
# Topic

Applies to: paths, behaviors and contracts governed here.
Read when: semantic triggers, including callers outside the directory.

## Confirmed facts
Evidence-backed descriptions, with stable repo-relative source references when useful.

## Rules
Only user-approved normative requirements; explain a surprising rule briefly.

## How to work here
Established commands, their working directory, and extension points, if relevant.

## Related context
Only required or useful links, with conditions for reading them.
```

Omit unused sections. Keep facts distinct from policies. Use file/symbol references rather than brittle line numbers. Historical ADRs explain decisions; superseded ADRs are not active rules. Never silently change historical rationale; propose a superseding decision or an explicitly approved correction. `CONTEXT.md` remains a glossary; architecture does not belong in it.

## Change proposal

Present in chat before a protected write:

- Operation and path(s), including source/destination for moves.
- Exact proposed content or diff; for deletion show what is removed.
- Reason and evidence; distinguish a new user policy from an observed fact.
- Applicability and affected links/callers; previous rule superseded if any.
- Explicit request to approve this package (or individual items).

Code work and a documentation proposal may be reported together. Approval to implement a feature is not approval of a proposal merely attached to its plan. Explicit approval of a concrete package that names the documentation operations is sufficient. Preserve independent task work if the user rejects the documentation changes.
