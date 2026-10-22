---
name: pr-review-orchestrator
description: Use when reviewing a GitHub PR end-to-end, posting PR comments, or when the user asks for a PR review - first runs the strict thermo-nuclear maintainability review over the full diff, then uses the GitHub PR review workflow only for approved comments.
---

# PR Review Orchestrator

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

This is the entry point for reviewing GitHub pull requests. It coordinates two stages:

1. Review the full PR diff with the strict maintainability bar from `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md`.
2. Convert only approved findings into GitHub review comments through `~/.wonsky-agents/skills/github-pr-review/SKILL.md`.

Prefer the strict review lens first. The posting skill is for mechanics, user voice, pending reviews, and GitHub API safety; it should not weaken the quality bar.

## Stage 1: Strict Diff Review

Before drafting public comments:

1. Read `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md`.
2. Read `~/.wonsky-agents/skills/github-pr-review/SKILL.md` for GitHub access rules, MCP preference, and PR context methods.
3. Verify GitHub access via the GitHub MCP server (`user-github`) when available; use `gh` only as fallback.
4. Fetch the complete PR context:
   - PR metadata and latest head SHA.
   - Full diff.
   - Changed files.
   - Existing review comments and reviews when relevant.
   - CI/check status when relevant to the review.
5. Load repository standards (`AGENTS.md` and linked convention docs) before judging architecture or style.
6. Apply the strict review skill to the full diff and produce candidate findings.

Candidate findings are not comments yet. They should include:

- file/path and diff location when available
- severity (`Critical`, `Important`, or `Minor`)
- the structural or behavioral problem
- why it matters
- the cleaner direction or suggested fix
- whether it should be a PR comment, overall summary note, or skipped

Do not produce low-value cosmetic nits if stricter structural findings exist.

## Stage 1 Approval

Show the candidate findings to the user before writing GitHub comments. Ask which findings should become comments.

Use `AskQuestion` when available:

- One option to approve all high-confidence comments.
- One option to approve selected comments only.
- One option to revise the draft first.
- One option to skip posting.

If the user approves only some findings, carry forward only those approved findings. Never post rejected or unapproved findings.

## Stage 2: Comment Drafting and Posting

After findings are approved:

1. Read and follow `~/.wonsky-agents/skills/github-pr-review/SKILL.md` completely.
2. Read `reviewer-preferences.md`.
3. Fetch recent samples of the user's real PR review comments and match that voice.
4. Convert approved findings into line-anchored comments or an overall review message.
5. Choose the event type deliberately:
   - `REQUEST_CHANGES` for blocking bugs, security issues, broken behavior, or serious maintainability regressions.
   - `COMMENT` for neutral feedback, questions, or when severity is unclear.
   - `APPROVE` only when remaining feedback is non-blocking and the PR is ready.
6. Show exactly what will be posted: file, line, body, suggestions, event type, and overall message.
7. Get explicit user approval via `AskQuestion`.
8. Post as a pending review, add approved comments, then submit the pending review.

The second approval is mandatory because Stage 1 approves findings, while Stage 2 approves exact public wording.

## Non-Negotiables

- Do not post comments directly from Stage 1 findings.
- Do not use the GitHub posting workflow as a substitute for strict diff review.
- Do not post any comment the user did not approve.
- Do not approve a PR merely because tests pass if the strict review finds serious structural regression.
- Do not dilute the strict review to match the author's implementation; push for simpler structure when a cleaner path is visible.
- If the user corrects tone or comment selection, update `reviewer-preferences.md` through the GitHub PR review skill's learning loop.

## Output Shape

Before Stage 1 approval:

```markdown
## Candidate Findings
- [Severity] `path`: issue, why it matters, recommended direction.

## Suggested Review Outcome
`REQUEST_CHANGES` / `COMMENT` / `APPROVE`, with 1 sentence why.
```

Before Stage 2 posting:

```markdown
## Review Draft
- `path:line` exact comment body

Event: `REQUEST_CHANGES` / `COMMENT` / `APPROVE`
Overall message: ...
```
