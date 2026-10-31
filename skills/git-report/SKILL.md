---
name: git-report
description: Generate a management-ready summary of work from git history. Use when the user asks for a report, weekly report, summary, status update, what they did this week, what was done, standup notes, or work log. Supports custom date ranges or defaults to the current week.
---

# Git Activity Report

Generate a concise, management-friendly summary of the user's work from git
history.

## 1. Establish scope, identity and dates

- Use the current date and timezone supplied by the user/host. If the user specifies a range, use it; otherwise use Monday through today, inclusive. Resolve ambiguous dates or timezone only when they affect the report.
- Confirm which repository and refs the report covers: the default branch, a named branch, or all relevant refs. State the choice. `--all` is not proof of merged delivery and can include local/stash refs.
- Resolve the user before running author-dependent queries. Prefer an explicit identity; inspect `git config user.name`, `git config user.email`, `.mailmap` and scoped author metadata as evidence. A configured account is a candidate, not proof of historical aliases. Never select the most frequent author as the user. Confirm ambiguous identities, and include verified aliases explicitly.
- Build explicit full-day bounds in the chosen timezone: start at `YYYY-MM-DDT00:00:00±HH:MM` and inclusive end at `YYYY-MM-DDT23:59:59±HH:MM`. Compute the offset for **each boundary date**, accounting for daylight saving changes. Do not pass date-only strings to Git. If the timezone cannot be resolved, ask or state an agreed UTC range instead of silently using the host timezone.
- Git log date limits filter commit/committer timestamps. State that basis; if the user specifically wants author-time activity, collect author timestamps and filter those explicitly instead.

## 2. Collect raw data

First gather scope and identity evidence. Once the refs, identities and exact bounds are resolved, run independent scoped queries in parallel. Substitute the verified revision arguments for `<REFS>` and full timestamps for the bounds:

```bash
# Commit evidence, including canonical author identity and both timestamps
git log <REFS> --since="<start-midnight-with-offset>" \
  --until="<end-23:59:59-with-offset>" \
  --format="%H%x09%aN%x09%aE%x09%aI%x09%cI%x09%s"

# Change statistics for the same bounded revision set
git log <REFS> --since="<start-midnight-with-offset>" \
  --until="<end-23:59:59-with-offset>" --numstat \
  --format="%H%x09%aN%x09%aE"
```

Filter the structured author identity against the exact verified email/name aliases, then retain the matching commit hashes for statistics and enrichment. If using `--author` as a query optimization, use literal matching and still validate the returned identities; substring matches can include another person. Avoid shell interpolation of user text. Exclude merge/stash bookkeeping based on Git metadata/ref scope, not by dropping every subject containing "Merge" or "WIP".

Deduplicate commit hashes across refs. Distinguish unique files from summed per-commit file touches, and state whether line totals include merges or renames. A missing remote connection or unfetched history is a coverage limit, not evidence that no work happened. Do not fetch or query unrelated repositories implicitly.

## 3. Enrich with PR context

A subject ending in `(#NNN)` is only a candidate reference. Read the commit body using `git show -s --format=%B <verified-hash>`; it is not necessarily a PR description or proof of merge. Fetch verified PR details through an available authenticated connector/CLI when authorized and useful. Only call work merged when base-branch/PR evidence establishes that state. Batch independent reads through the tool interface, without shell separator commands. If PR access is unavailable, report commit-based evidence and its limits.

## 4. Produce the report

Format the output as below. Tone: professional, factual, no fluff.

```
**Accomplishments — <Full Name> (<date range>)**

1. **<Feature / PR title>** — one-line summary
   - Bullet of what was done
   - Bullet of what was done

2. **<Next feature>** — one-line summary
   - …

3. **CI / Code Quality / Misc** (group small fixes here)
   - …

4. **In Progress** (if any branches have commits but no merged PR)
   - …

---
Stats: <measured unique files or commit touches>, <measured line totals>, <verified PR/commit count>.
Scope: <repository/refs>, <dates and timezone>, <committer-time or author-time basis>.
```

### Grouping rules

| Category | What goes in |
|----------|-------------|
| Feature / PR | Group verified related commits or a verified merged PR; label the evidence accurately. |
| CI / Code Quality | Commits like "fix ci", "copilot comments", "fix style" — group together. |
| In Progress | Work verified as unmerged on the relevant branch; absence of a fetched PR is insufficient. |

### Writing rules

- Lead each item with a **bold title** and a short plain-English summary.
- Sub-bullets for specifics (what was built, what changed, why it matters).
- Quantify where possible ("added 5 API endpoints", "migrated 12 models").
- Omit merge commits, stash entries, and trivial one-liners from individual
  items — roll them into the CI/Quality bucket.
- Keep the whole report under ~30 lines — scannable in 60 seconds.
