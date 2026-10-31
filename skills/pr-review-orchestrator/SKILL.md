---
name: pr-review-orchestrator
description: Use when reviewing a GitHub PR end-to-end, posting PR comments, or when the user asks for a PR review - first runs the strict thermo-nuclear maintainability review over the full diff, then uses the GitHub PR review workflow only for approved comments.
---

# PR Review Orchestrator

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

This is the entry point for reviewing GitHub pull requests. A plain review request is analysis-only: deliver findings in chat without creating pending reviews, comments or other external writes. Stage 2 applies only when the user explicitly requests public posting and approves the exact wording/event. Reuse existing authorization for that exact unchanged draft. It coordinates two stages:

1. Review the full PR diff with the strict maintainability bar from `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md`.
2. When public posting is explicitly authorized, convert only approved findings into GitHub review comments through `~/.wonsky-agents/skills/github-pr-review/SKILL.md`.

Prefer the strict review lens first. The posting skill is for mechanics, user voice, pending reviews, and GitHub API safety; it should not weaken the quality bar.

## Stage 1: Strict Diff Review

Before drafting public comments:

1. Read `~/.wonsky-agents/skills/strict-code-quality-review/SKILL.md`.
2. Read `~/.wonsky-agents/skills/github-pr-review/SKILL.md` for GitHub access rules, MCP preference, and PR context methods.
3. When fetching is needed, prefer available GitHub connector tools; use `gh` as fallback. Tool/server names vary by host. A supplied offline diff remains reviewable without GitHub access; disclose missing context and head identity rather than blocking analysis or inventing them.
4. For an online review, fetch the complete authorized PR context; for a supplied offline diff, review the available evidence and state its limits:
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

For analysis-only work, deliver the findings and stop without prompting for public posting. If public posting was requested, show candidate findings and ask which should become comments.

Use an available host question tool or ordinary chat, rather than requiring a tool named `AskQuestion`:

- One option to approve all high-confidence comments.
- One option to approve selected comments only.
- One option to revise the draft first.
- One option to skip posting.

If the user approves only some findings, carry forward only those approved findings. Never post rejected or unapproved findings.

## Stage 2: Comment Drafting and Posting

After public posting is explicitly requested and the intended findings are approved:

1. Read and follow `~/.wonsky-agents/skills/github-pr-review/SKILL.md` completely.
2. Follow that skill's conditional canonical private-preference and voice-calibration procedure. A missing private profile does not block drafting; do not assume a sibling runtime file is the source.
3. Reuse applicable session preferences and current examples. Obtain fresh remote samples only when that procedure calls for calibration and the read is authorized; do not fetch them for every draft.
4. Convert approved findings into line-anchored comments or an overall review message.
5. Choose the event type deliberately:
   - `REQUEST_CHANGES` for blocking bugs, security issues, broken behavior, or serious maintainability regressions.
   - `COMMENT` for neutral feedback, questions, or when severity is unclear.
   - `APPROVE` only when remaining feedback is non-blocking and the PR is ready.
6. Show exactly what will be posted: file, line, body, suggestions, event type, and overall message.
7. Obtain explicit approval of the exact public draft and event using an available question tool or chat; do not ask again for the exact unchanged draft already approved.
8. Post as a pending review, add approved comments, then submit the pending review.

Finding selection alone does not approve public wording. Approval must cover the exact draft and event before creating or submitting a pending review. Recheck the PR head/diff anchors immediately before posting; if they changed, refresh the affected evidence and obtain approval for materially changed text or locations.

## Non-Negotiables

- Do not create pending reviews or post comments for analysis-only work or directly from unapproved Stage 1 findings.
- Do not use the GitHub posting workflow as a substitute for strict diff review.
- Do not post any comment the user did not approve.
- Do not approve a PR merely because tests pass if the strict review finds serious structural regression.
- Do not dilute the strict review to match the author's implementation; push for simpler structure when a cleaner path is visible.
- If the user corrects tone or comment selection, follow the GitHub PR review skill's canonical private-preference learning procedure and its applicable approval boundary; never edit a generated runtime mirror.

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
