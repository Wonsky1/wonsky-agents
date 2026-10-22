---
name: git-report
description: Generate a management-ready summary of work from git history. Use when the user asks for a report, weekly report, summary, status update, what they did this week, what was done, standup notes, or work log. Supports custom date ranges or defaults to the current week.
---

# Git Activity Report

Generate a concise, management-friendly summary of the user's work from git
history.

## 1. Determine the date range

- The current date and day of the week are available in the system prompt
  (`Today's date:`). Use them.
- **If the user specifies a range** (e.g., "last 2 weeks", "since March 1",
  "yesterday"), — use that range.
- **If the user says "this week"** or gives no range — use Monday of the
  current week through today (inclusive). For example if today is Wednesday
  Apr 9, the range is Apr 7 – Apr 9.
- Convert to git flags: `--since="YYYY-MM-DD"` (start) and
  `--until="YYYY-MM-DD"` (day after end, to make the range inclusive).

## 2. Collect raw data

Run **all three** commands in parallel:

```bash
# All commits with authors (to identify the user's name)
git log --all --since="<start>" --until="<day_after_end>" \
  --format="%h %ad %an %s" --date=short

# User's commits only, excluding merges/stash entries
git log --all --since="<start>" --until="<day_after_end>" \
  --author="<user>" --format="%h %ad %s" --date=short \
  | grep -v "Merge\|WIP on\|index on"

# Diff stats for the user's commits
git log --all --since="<start>" --until="<day_after_end>" \
  --author="<user>" --shortstat --oneline
```

To resolve `<user>`, pick the most-frequent non-bot author name from the first
command, or use the name/email from `git config user.name`.

## 3. Enrich with PR context

For every merged PR hash (commits ending with `(#NNN)`), fetch the full commit
body to extract the PR description:

```bash
git log <hash> --format="%B" -1
```

Batch multiple hashes into a single shell command separated by `echo "---"`.

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
Stats: ~X files touched, ~Y lines added across N merged PRs.
```

### Grouping rules

| Category | What goes in |
|----------|-------------|
| Feature / PR | Each merged PR gets its own numbered item. Title from the PR commit message. |
| CI / Code Quality | Commits like "fix ci", "copilot comments", "fix style" — group together. |
| In Progress | Branches with commits but no merged PR in the period. |

### Writing rules

- Lead each item with a **bold title** and a short plain-English summary.
- Sub-bullets for specifics (what was built, what changed, why it matters).
- Quantify where possible ("added 5 API endpoints", "migrated 12 models").
- Omit merge commits, stash entries, and trivial one-liners from individual
  items — roll them into the CI/Quality bucket.
- Keep the whole report under ~30 lines — scannable in 60 seconds.
