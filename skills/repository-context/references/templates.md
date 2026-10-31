# Repository context templates

Use these as a selection guide for evidence-backed context drafts, not a form to fill. Follow SKILL.md's draft-first review workflow and its separate approval gate for active instructions and existing user rules. Reuse established locations and accurate documentation.

## Thin root AGENTS.md

Keep only repository-wide invariants, critical constraints and context links. New factual setup may begin with this neutral entry point:

```markdown
# Repository context

Draft — awaiting user review. This entry links descriptive context; proposed policies in drafts are not active instructions.

Context index: [Repository context](docs/agent-context/index.md).
```

If AGENTS.md exists, preserve its rules and present the exact proposed context-link addition for approval. Do not replace it with this template. Approved rules may be added only through the exact instruction-change gate. Product instructions stay repository-relative and portable; do not require another contributor's personal skill installation.

## Context index

Select documents by task meaning or affected paths, then follow required dependencies. Use only rows for real useful documents, including existing docs. Mark new draft entries clearly. Example:

```markdown
# Context index

Draft — awaiting user review. Read relevant topics and required links. Existing repository instructions retain their authority.

| Read when | Applies to | Document | Review status |
|---|---|---|---|
| Changing boundaries or integration contracts | Cross-component work | [Architecture](architecture.md) | Draft |
| Implementing or verifying code | Development work | [Development](development.md) | Draft |
```

The index can link a glossary, an individual relevant ADR or an existing guide. Avoid competing maps and empty example topics. A nested index is useful only when navigation needs it.

## Context module

Capture useful confirmed knowledge even when it needs several paragraphs. Keep statements short and group cohesive topics. Use only sections that help:

```markdown
# Topic

Draft — awaiting user review.

Applies to: relevant behavior, contracts and paths.
Read when: semantic triggers, including cross-component callers.

## Confirmed facts and requirements
Evidence-backed behavior, responsibilities and constraints; stable source references when useful.

## Design and integration
Important patterns, boundaries, contracts, reasons and extension points.

## How to work here
Established commands and their working directory when useful.

## Open questions or proposed policies
Explicitly unresolved questions. Mark each proposed rule: Proposed policy — not active.

## Related context
Only useful links, with reading conditions.
```

Remove unused headings and placeholders. Facts, user-approved rules and proposed policies remain distinct. Preserve historical ADR rationale and established glossary meanings; changes to those require exact approval. A draft is for review, not authority.

## Review request and instruction proposal

After writing factual drafts, show the actual paths and diff, summarize the evidence and explicitly ask whether the context is correct and complete. Report draft-awaiting-review until the user reviews it. Apply corrections and remove draft markers only under that concrete review approval.

For existing instruction/policy changes, present the exact operation, path, content/diff, reason, evidence, applicability and affected links **before writing**, then wait for approval. Include removals/moves explicitly. A reviewed context draft does not authorize unrelated policies. Follow SKILL.md for updated, verified-current, draft-awaiting-review, pending-approval and declined outcomes.
