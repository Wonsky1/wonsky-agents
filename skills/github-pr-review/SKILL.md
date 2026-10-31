---
name: github-pr-review
description: Draft and post approved GitHub PR review comments using the GitHub MCP server (preferred) or gh fallback - creates pending reviews, batches comments, chooses event types, applies reviewer-preferences, and learns from corrections. Use directly for posting approved comments; for end-to-end PR review start with pr-review-orchestrator.
---

# GitHub PR Review

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

Workflow for drafting and posting GitHub pull request review comments using **pending** reviews with batched comments and code suggestions. Always batch — even under time pressure, even for a single comment.

For end-to-end PR review, start with `~/.wonsky-agents/skills/pr-review-orchestrator/SKILL.md`. That orchestrator runs the strict diff review first, then returns here only for approved comments and safe GitHub posting.

**Prefer an available GitHub connector** for supported PR operations. Discover its current tool names and schemas; `user-github` and the calls below are examples, not host requirements. Fall back to authenticated `gh` when the connector lacks a required operation. A supplied offline diff can still be reviewed when neither can fetch or post; state that remote head, anchors and posting remain unverified.

**Always obtain explicit approval of the exact review before posting.** Show the repository/PR, reviewed head SHA, each file/line/side, exact comment text, event type and overall message. Use the host's available question tool or ask in chat, then wait for an explicit answer. Approval of a review idea alone does not authorize its wording.

**Read the user's private review preferences before drafting when available.** Resolve `WONSKY_AGENTS_HOME` (default `~/.wonsky-agents`) and prefer `<canonical-root>/skills/github-pr-review/reviewer-preferences.md`; a sibling runtime profile is a read-only fallback. An absent profile is normal on a fresh install: use explicit session preferences without inventing a profile. Do not publish, commit or include private profile text in review payloads.

**Calibrate voice proportionately.** Reuse preferences and recent examples already read in this session. Fetch a small relevant sample of the user's own comments only when preferences are missing, stale, contradictory or the user asks for calibration. Resolve the authenticated/reviewing identity first, restrict the sample to that user's comments, and exclude the PR under review. Observed examples inform tone; explicit current preferences win. Do not copy private source text into a public comment.

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

Discover the host's connected GitHub tools and inspect their current schemas. Do not read another machine's MCP descriptor paths. The following names illustrate one server's capabilities; adapt to the actual connector.

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

If neither connector nor `gh` is available, explain which remote operations are unavailable. Continue an authorized read-only review from a supplied diff or local checkout when possible; label head/anchor/CI evidence that could not be checked. For posting, ask the user to connect GitHub or authenticate an installed CLI. Do not fabricate remote state or install tools without authorization.

## Core Workflow

**Required steps — do not skip any:**

1. **Establish access and identity** — discover connected tools or check `gh auth status`; for offline input, record what cannot be verified remotely.
2. **Load preferences** — use the canonical private profile when present and explicit session preferences. Read the applicable repository guidance through the existing context packet.
3. **Calibrate only when needed** — reuse current examples or obtain a small sample as described above.
4. **Fetch PR context** — repository/PR identity, diff, changed files, head SHA, existing reviews and relevant CI. An offline draft remains unverified for posting until these can be checked.
5. **Draft** — line-anchored comments, suggestions if appropriate, event and overall message. Match actual standards and user preferences; distinguish evidence from speculation.
6. **Present the exact payload and reviewed SHA**, ask for approval and wait.
7. **Revalidate before mutation** — refetch the head and affected diff anchors. If the head, comment text/anchors, event or message changed, show the revised package and obtain approval again.
8. **Use a pending review, then submit** — inspect existing pending reviews first; never append to, submit or delete an unrelated draft. Keep the ID of the review created for this approved package. Confirm staged comments and overall message match the approval, then recheck the head before submission. If the connector cannot safely identify the intended pending review, use a supported alternative or stop posting and report the limitation.
9. **Report the actual result** — include the submitted review link when available; partial staging is not a posted review. On a changed head or failed operation, retain the known state and explain it instead of retrying into a different draft.
10. **If the user corrects the draft**, apply the preference in this session immediately, follow the persistence gate below, and obtain approval of the revised public payload.

### Approval pattern

Before posting **any** review, present:

- Repository/PR identity and reviewed head SHA
- File path, line number/range and side for each comment
- Exact comment body (including any `suggestion` block)
- Event type (`APPROVE` / `REQUEST_CHANGES` / `COMMENT`)
- Overall review message

Then use the available question tool or ask in chat:

- Question: "Post this review as shown?"
- Options: `Yes, post it as shown` / `No, let me revise first`

Only proceed on explicit yes.

## Personal Preferences & Learning Loop

The canonical private profile described above records focus areas, tone, suggestion patterns, severity, exclusions and project-specific preferences. Its absence must not block drafting. It is local user data, excluded from version control.

1. Read relevant existing preferences without exposing them publicly.
2. Apply a correction to the active draft immediately. For a lasting profile change, reread the relevant section, remove duplication, and present the canonical path and exact 1–2-line change. Follow the `repository-context` approval gate, unless an explicit standing user instruction already authorizes this particular correction log and operation. Do not interpret permission to post a review as permission to change lasting instructions.
3. Apply only approved profile changes at the canonical source, never to a generated runtime copy. If the source or approval is unavailable, keep the preference in session and report persistence as pending. Use the installer for any later synchronization and preserve destination conflicts.
4. Re-draft and request approval of the exact public review again. A private learning change never grants authority to post.

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

**Omit `event`** to create a pending review. Retain the returned review ID and verify it belongs to this package. Some connectors scope follow-up calls to the current user's pending review rather than an ID; inspect that draft before calling them, and do not use them if ownership cannot be established safely.

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

If the user revokes approval after this workflow created a pending review, first verify its ID and contents. Delete only that draft, leaving any pre-existing draft untouched. With a connector whose verified schema uses the following call:

```json
{ "method": "delete_pending", "owner": "<owner>", "repo": "<repo>", "pullNumber": <number> }
```

## Fallback Workflow — `gh` CLI

Only use if the MCP is unavailable. Run via the Shell tool.

Prepare a UTF-8 JSON file with the **approved** `commit_id` and `comments` array (`path`, `line`, `side`, `body`, and range fields when needed). Use a file-writing API or a safely quoted literal heredoc so comment bodies cannot execute as shell code. Preserve real newlines in JSON strings through a JSON serializer.

```bash
gh pr view <PR_NUMBER> --repo <OWNER/REPO> --json headRefOid
gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/reviews
gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/reviews \
  --method POST --input "approved-review.json"
```

Omit `event` from the creation payload to keep it pending. Record the returned review ID and validate its comments against the approval. After the head and anchors are rechecked, prepare an approved submit JSON file containing `event` and `body`:

```bash
gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/reviews/<REVIEW_ID>/events \
  --method POST --input "approved-submit.json"
```

Use explicit owner/repository identity throughout. Never let a different current working directory select the target. Read the installed CLI help/API response for supported fields rather than guessing.

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
| Posting without user approval                          | Present exact payload and wait for approval — reviews are external writes |

## Red Flags — Stop If You're Thinking…

- "User said ASAP, so I'll skip pending review"
- "Only one comment, so I'll post directly"
- "User already approved the *idea* of a review, so I can skip the approval question"
- "I'll post it and then tell them what I posted"
- "The approval step slows things down"
- "I'll check MCP/gh later — let me draft first"
- "The MCP is probably connected, no need to verify"

**All of these mean: check access and actual draft state, present the exact payload, wait for approval, then post through a verified pending review.**

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

### Step 2 — Present the draft and ask for approval

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

Use the available question tool or ask in chat:

- Question: "Post this review as shown?"
- Options: `Yes, post it` / `No, let me revise`

### Step 3 — After explicit "Yes", revalidate head/anchors and pending-review ownership, then post via MCP

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
