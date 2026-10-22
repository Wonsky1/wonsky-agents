---
name: github-pr-review
description: Draft and post approved GitHub PR review comments using the GitHub MCP server (preferred) or gh fallback - creates pending reviews, batches comments, chooses event types, applies reviewer-preferences, and learns from corrections. Use directly for posting approved comments; for end-to-end PR review start with pr-review-orchestrator.
---

# GitHub PR Review

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Persistent repository instructions/context may change only under that skill's concrete-proposal approval gate.

Workflow for drafting and posting GitHub pull request review comments using **pending** reviews with batched comments and code suggestions. Always batch — even under time pressure, even for a single comment.

For end-to-end PR review, start with `~/.wonsky-agents/skills/pr-review-orchestrator/SKILL.md`. That orchestrator runs the strict diff review first, then returns here only for approved comments and safe GitHub posting.

**Prefer the GitHub MCP server** (`user-github`) for all PR operations. Fall back to the `gh` CLI only if the MCP is unavailable.

**CRITICAL: Always get explicit user approval via the `AskQuestion` tool before posting any review.** Show exactly what will be posted (file, line, comment text, event type) and ask yes/no.

**ALWAYS read `reviewer-preferences.md` (sibling of this file) before drafting any review** — it captures the user's style, focus areas, severity calibration, and things to skip. Apply those preferences to every draft.

**ALSO fetch a recent sample of the user's actual review comments** on the target repo before drafting — the seeded preferences age fast and the user's real voice on recent PRs is the ground truth. Use the GitHub MCP:

1. `search_pull_requests` with `query: "is:pr reviewed-by:<user> sort:updated-desc"`, `perPage: 10`.
2. For the 5–8 most recent PRs (excluding the one you're about to review), call `pull_request_read` with `method: get_review_comments` and keep only entries where `author == <user>`.
3. Calibrate your draft's length, formatting, tone, severity, and use of `suggestion` blocks to match those samples — not just the seeded style guide.

If the sample shows the user writes 5–15-word, lowercase, plain-prose comments without markdown formatting or `suggestion` blocks, your draft must look the same. If a seeded preference and a recent sample disagree, the recent sample wins.

**Repository standards win over legacy precedent.** Read the repo's `AGENTS.md` and any docs under `docs/conventions/` before drafting. If the PR adds code that follows a wrong pattern already present in the file (e.g. legacy router with inline Pydantic models, `datetime.utcnow()`, bare string literals, `await db.commit()` inside services), still flag it — explain that the existing code is non-compliant and the *new* code should follow the standard, even if the file around it does not. Never validate violations by saying "the rest of the file does this too." Suggest the correct pattern in the `suggestion` block.

**Related skills:**
- For reviewing an in-progress branch before merge, see `~/.wonsky-agents/skills/requesting-code-review/SKILL.md`.
- For handling feedback you receive on your own PR, see `~/.wonsky-agents/skills/receiving-code-review/SKILL.md`.

## When to Use

- Drafting comments from already-approved PR review findings
- Adding approved code suggestions to a PR (GitHub `suggestion` block syntax)
- Posting approved review comments on a PR

For a full review from scratch, use `~/.wonsky-agents/skills/pr-review-orchestrator/SKILL.md` first. Use this skill directly when the findings/comments are already approved or the user only needs posting mechanics.

## Prerequisites

### Preferred: GitHub MCP server

Check the `user-github` MCP server is enabled and connected. Tool descriptors live at:

```
/Users/vpidborsky001/.cursor/projects/.../mcps/user-github/tools/
```

The tools you will use most:

| Tool                              | Purpose                                                            |
|-----------------------------------|--------------------------------------------------------------------|
| `get_me`                          | Verify auth — call once at session start                           |
| `pull_request_read`               | Fetch PR details, diff, files, existing reviews/comments           |
| `pull_request_review_write`       | Create pending review, submit it, delete it, resolve/unresolve threads |
| `add_comment_to_pending_review`   | Add a line-anchored comment (with optional `suggestion` block) to the current pending review |

### Fallback: `gh` CLI

If the MCP server is not connected, verify `gh` is installed and authenticated via the Shell tool:

```bash
gh --version && gh auth status
```

If neither MCP nor `gh` is available, stop and tell the user:

```
Cannot review the PR — neither the GitHub MCP server nor the gh CLI is available.

Options:
- Enable the user-github MCP server in ~/.cursor/mcp.json, OR
- Install the GitHub CLI from https://cli.github.com/ and run `gh auth login`.
```

Do not attempt to fabricate review output.

## Core Workflow

**Required steps — do not skip any:**

1. **Verify access** — MCP (`get_me`) or `gh` (`gh auth status`).
2. **Load reviewer preferences** — read `reviewer-preferences.md` (sibling file). Use it to shape what you flag, how you phrase comments, which severity to choose, and what to skip.
3. **Fetch recent voice samples** — call `search_pull_requests` with `query: "is:pr reviewed-by:<user> sort:updated-desc"` (excluding the PR under review), then `pull_request_read get_review_comments` on the 5–8 newest, filtering to the user's own comments. Use these as the ground truth for length, formatting, severity, and `suggestion` usage. Recent samples override seeded preferences when they disagree.
4. **Load repository standards** — read the PR's repo `AGENTS.md` (root) and any linked convention files under `docs/conventions/`. Treat these as the authoritative ruleset. New code must follow them even if surrounding legacy code does not.
5. **Fetch PR context** — diff, changed files, latest commit SHA.
6. **Draft the review** — line-anchored comments + optional code suggestions + chosen event type + overall message. Apply preferences AND match the recent-sample voice. When the PR follows an existing wrong pattern, flag it in the user's voice and don't cite AGENTS.md in the comment text unless the user does.
7. **Show the user exactly what will be posted** — call `AskQuestion` with a yes/no choice.
8. **Wait for explicit approval** — do not post on assumption.
9. **Post as PENDING, then submit** — never post comments outside a pending review.
10. **If the user corrects you during steps 7–9** — append the correction to `reviewer-preferences.md` per the Learning Loop section in that file. Do this **silently** (no permission needed). Then re-draft.

### Approval pattern

Before posting **any** review, present:

- File path and line number for each comment
- Exact comment body (including any `suggestion` block)
- Event type (`APPROVE` / `REQUEST_CHANGES` / `COMMENT`)
- Overall review message

Then call `AskQuestion`:

- Question: "Post this review as shown?"
- Options: `Yes, post it as shown` / `No, let me revise first`

Only proceed on explicit yes.

## Personal Preferences & Learning Loop

The file `reviewer-preferences.md` (sibling of this `SKILL.md`) is the user's personal review style guide. It contains:

- **Focus Areas** — things the user always wants flagged
- **Style & Tone** — how comments should sound
- **Suggestion Patterns** — conventions for `suggestion` blocks
- **Severity Calibration** — when to use `APPROVE` vs `REQUEST_CHANGES` vs `COMMENT`
- **Things to Skip** — areas to never comment on (e.g. lockfiles)
- **Project-Specific Conventions** — rules tied to the user's projects
- **Corrections log** — chronological record of pushbacks

### Required behavior

1. **Read the file at step 2 of every review**, before drafting anything. Apply every relevant section to the draft.
2. **When the user corrects, rejects, or refines a drafted comment**, append a new entry to the appropriate section of `reviewer-preferences.md`:
   - Use the existing section headers; only add a new section if no existing one fits.
   - Append silently — do not ask permission.
   - Keep entries to 1–2 lines.
   - Don't duplicate existing entries — re-read the section first.
3. **Then re-draft** the review with the new preference applied, and run the approval step again.

The intent: every review converges closer to how the user would have written it themselves.

## Preferred Workflow — GitHub MCP

### Step 1 — Gather PR context

Call `pull_request_read` with the appropriate method:

| Need                      | `method`              |
|---------------------------|-----------------------|
| Basic PR info + head SHA  | `get`                 |
| Full diff                 | `get_diff`            |
| List of changed files     | `get_files`           |
| Existing review threads   | `get_review_comments` |
| Existing reviews          | `get_reviews`         |
| CI status                 | `get_check_runs`      |

Always required: `owner`, `repo`, `pullNumber`.

### Step 2 — Create the PENDING review

Call `pull_request_review_write` with:

```json
{
  "method": "create",
  "owner": "<owner>",
  "repo": "<repo>",
  "pullNumber": <number>,
  "commitID": "<latest_head_sha>"
}
```

**Omit `event`** — that's what makes it pending. The response includes the review ID (not needed for follow-up calls; the MCP scopes by "current user's pending review").

### Step 3 — Add comments to the pending review

For each comment, call `add_comment_to_pending_review`:

```json
{
  "owner": "<owner>",
  "repo": "<repo>",
  "pullNumber": <number>,
  "path": "src/auth.ts",
  "line": 42,
  "side": "RIGHT",
  "subjectType": "LINE",
  "body": "Explanation.\n\n```suggestion\nfixed code here\n```\n\nOptional follow-up context."
}
```

| Field        | Notes                                                                       |
|--------------|-----------------------------------------------------------------------------|
| `path`       | Repo-relative file path                                                     |
| `line`       | End line of the comment (last line for multi-line)                          |
| `side`       | `RIGHT` for added/modified lines (most common), `LEFT` for deleted lines    |
| `subjectType`| `LINE` (most common) or `FILE` for file-level comments                      |
| `startLine`  | Optional, first line of range (for multi-line suggestions)                  |
| `startSide`  | Optional, paired with `startLine`                                           |
| `body`       | Markdown; include `suggestion` block for code suggestions (see below)       |

### Step 4 — Submit the pending review

Call `pull_request_review_write` again with:

```json
{
  "method": "submit_pending",
  "owner": "<owner>",
  "repo": "<repo>",
  "pullNumber": <number>,
  "event": "REQUEST_CHANGES",
  "body": "Overall review message visible at the top of the review."
}
```

### Bonus: Resolve threads after they're addressed

To resolve a thread without leaving a "fixed" reply comment, call `pull_request_review_write`:

```json
{ "method": "resolve_thread", "threadId": "PRRT_kwDOxxx", "owner": "<owner>", "repo": "<repo>", "pullNumber": <number> }
```

Get thread IDs from `pull_request_read` with `method=get_review_comments`.

### Bonus: Cancel a pending review

If the user revokes approval after a pending review was created, call:

```json
{ "method": "delete_pending", "owner": "<owner>", "repo": "<repo>", "pullNumber": <number> }
```

## Fallback Workflow — `gh` CLI

Only use if the MCP is unavailable. Run via the Shell tool.

```bash
# Get the latest commit SHA on the PR
gh pr view <PR_NUMBER> --json commits --jq '.commits[-1].oid'

# Create the PENDING review with all comments (no event field = pending)
gh api repos/:owner/:repo/pulls/<PR_NUMBER>/reviews \
  -X POST \
  -f commit_id="<COMMIT_SHA>" \
  -f 'comments[][path]=path/to/file.ts' \
  -F 'comments[][line]=42' \
  -f 'comments[][side]=RIGHT' \
  -f 'comments[][body]=Comment body with optional suggestion block' \
  --jq '{id, state}'
# Returns: {"id": <REVIEW_ID>, "state": "PENDING"}

# Submit the pending review with chosen event type
gh api repos/:owner/:repo/pulls/<PR_NUMBER>/reviews/<REVIEW_ID>/events \
  -X POST \
  -f event="COMMENT" \
  -f body="Overall review message"
```

### `gh` syntax rules

- Use **single quotes** around any parameter with `[]`: `'comments[][path]=...'`
- Use `-f` for **string** values, `-F` for **numeric** values (line numbers especially)
- `gh` auto-detects `owner/repo` when run inside the repo working directory

## Event Types

Choose deliberately when submitting:

| Event              | Use when                                              | Examples                                        |
|--------------------|-------------------------------------------------------|-------------------------------------------------|
| `APPROVE`          | Non-blocking suggestions; PR is ready to merge        | Minor style, optional refactors, naming nits    |
| `REQUEST_CHANGES`  | Blocking issues that must be fixed                    | Bugs, security issues, broken tests, regressions|
| `COMMENT`          | Neutral feedback or questions, no approval signal     | Clarifying questions, neutral observations      |

If unsure, prefer `COMMENT` — never auto-approve.

## Code Suggestions

A code suggestion replaces the targeted line(s) when the PR author clicks "Commit suggestion". Embed inside the comment `body`:

```
Brief explanation of the issue.

```suggestion
const fixed = "replacement code";
```

Optional context after the suggestion.
```

The suggested code must be **complete** for the line range it replaces — no half-statements, no `// ...` placeholders.

### Edge case: suggestions inside markdown / nested fences

When the file being reviewed is markdown or already contains triple backticks, use 4 backticks (or tildes) around the `suggestion` fence to avoid conflicts:

`````
````suggestion
```javascript
const example = "nested fenced code";
```
````
`````

## Common Mistakes

| Mistake                                                | Fix                                                                       |
|--------------------------------------------------------|---------------------------------------------------------------------------|
| Posting immediately under time pressure                | Still create pending first — submit step is one extra call                |
| "Only one comment, no need for pending"                | Use pending anyway — consistent workflow, lets you add more if you spot something |
| Using `gh api` when the MCP is connected               | Prefer the MCP — no shell escaping, structured arguments                  |
| Forgetting single quotes around `comments[][]` in `gh` | Always quote: `'comments[][path]=...'`                                    |
| Mixing up `-f` and `-F` in `gh`                        | `-F` for numbers (line numbers), `-f` for strings                         |
| Skipping the commit SHA lookup                         | Required for `gh`; for MCP, get via `pull_request_read` method `get`      |
| Wrong event type                                       | Bugs/security → `REQUEST_CHANGES`; style/optional → `APPROVE`; questions → `COMMENT` |
| Posting without user approval                          | Always use `AskQuestion` first — review comments are public and permanent |

## Red Flags — Stop If You're Thinking…

- "User said ASAP, so I'll skip pending review"
- "Only one comment, so I'll post directly"
- "User already approved the *idea* of a review, so I can skip the approval question"
- "I'll post it and then tell them what I posted"
- "The approval step slows things down"
- "I'll check MCP/gh later — let me draft first"
- "The MCP is probably connected, no need to verify"

**All of these mean: STOP. Verify access first, draft, get explicit approval via `AskQuestion`, then post as PENDING and submit.**

### Why pending reviews?

One extra call, but you get:

- Ability to add more comments if you spot additional issues mid-review
- Ability to re-read your own comments before they go public
- A single notification for the PR author (vs. one per comment)
- Consistent workflow regardless of perceived urgency

### Why explicit approval?

- Review comments are **public and permanent** on the PR
- Code suggestions can be subtly wrong
- Tone may need adjusting (especially for `REQUEST_CHANGES`)
- The user may want to refine the overall message

## Complete Example (MCP path)

### Step 1 — Gather context

```
pull_request_read(method="get", owner="acme", repo="api", pullNumber=123)
pull_request_read(method="get_diff", owner="acme", repo="api", pullNumber=123)
```

### Step 2 — Draft and ask via `AskQuestion`

Present the user with:

```
PR #123 review draft (3 comments, REQUEST_CHANGES):

Comment 1 — src/auth.ts:20
  "Token expiry validation is missing.
   ```suggestion
   if (Date.now() >= token.expiresAt) throw new TokenExpiredError();
   ```"

Comment 2 — src/auth.ts:35
  "Missing error handling for failed refresh.
   ```suggestion
   try { ... } catch (err) { logger.error({ err }, 'refresh failed'); throw err; }
   ```"

Comment 3 — tests/auth.test.ts:12
  "Missing test for the expired-token path."

Event: REQUEST_CHANGES
Overall: "Found 3 issues that should be addressed before merging."
```

Call `AskQuestion`:

- Question: "Post this review as shown?"
- Options: `Yes, post it` / `No, let me revise`

### Step 3 — After explicit "Yes", post via MCP

```
# Create pending
pull_request_review_write(
  method="create",
  owner="acme", repo="api", pullNumber=123,
  commitID="<sha from step 1>"
)

# Add each comment
add_comment_to_pending_review(
  owner="acme", repo="api", pullNumber=123,
  path="src/auth.ts", line=20, side="RIGHT", subjectType="LINE",
  body="Token expiry validation is missing.\n\n```suggestion\nif (Date.now() >= token.expiresAt) throw new TokenExpiredError();\n```"
)
add_comment_to_pending_review(
  owner="acme", repo="api", pullNumber=123,
  path="src/auth.ts", line=35, side="RIGHT", subjectType="LINE",
  body="Missing error handling for failed refresh.\n\n```suggestion\ntry { ... } catch (err) { logger.error({ err }, 'refresh failed'); throw err; }\n```"
)
add_comment_to_pending_review(
  owner="acme", repo="api", pullNumber=123,
  path="tests/auth.test.ts", line=12, side="RIGHT", subjectType="LINE",
  body="Missing test for the expired-token path."
)

# Submit
pull_request_review_write(
  method="submit_pending",
  owner="acme", repo="api", pullNumber=123,
  event="REQUEST_CHANGES",
  body="Found 3 issues that should be addressed before merging."
)
```

## Real-World Impact

**Without this pattern:**

- Multiple separate notifications spam the PR author
- Easy to forget issues while reviewing line by line
- Inconsistent workflow that drifts under pressure
- Public comments posted before the user has seen them
- Shell-escaping bugs in `gh api` calls (mis-quoted brackets, `-f` vs `-F` mix-ups)

**With this pattern:**

- All feedback lands in one coherent review
- PR author gets a single notification with full context
- Comments are user-approved before going public
- Native MCP arguments — no shell escaping required
- Professional, predictable reviews — every time
