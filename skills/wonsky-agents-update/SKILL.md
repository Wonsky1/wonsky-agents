---
name: wonsky-agents-update
description: Use when the user asks to update, refresh or upgrade an installed Wonsky Agents skill collection, or review local changes before an update. Preserve personal skills and instructions, preview file differences, and apply only the user's Keep or Use New choices.
---

# Update Wonsky Agents

Use the Python updater for source acquisition, OS/agent detection, comparison, backups and copying. This skill is a chat entry point, not a second installer or an LLM merge procedure.

## Locate and preview

1. Resolve the canonical collection from `WONSKY_AGENTS_HOME`, otherwise the user's home plus `.wonsky-agents`. Confirm the intended collection and destinations; a same-name skill folder does not prove ownership.
2. Read its README update section and `update.py --help`. Use an available Python 3.9+ interpreter (`python3`/`python`, or `py -3` on Windows). If a legacy installation lacks the updater, use `update.py` from a trusted new download to review that canonical installation; do not replace old files manually to bootstrap it.
3. Preview without changing installed files and save the local report outside version control:

```sh
python3 <updater-directory>/update.py --dry-run --report <local-review.json>
```

The default source is Wonsky1/wonsky-agents `main`, resolved to a pinned revision for that download. Use `--from <new-extracted-collection>` for a local source, `--baseline <trusted-old-collection>` for a known legacy original, and `--targets cursor,claude,codex,antigravity,agents` or `--all` only for the intended destinations. `--terminal` selects terminal interaction. Keep these source/destination options consistent through review and apply.

4. Present every affected skill and changed distributed file, including edits, additions and deletions. Show the exact local edits and offered upstream differences, distinguishing canonical and runtime destinations. If the original cannot be recovered, say **Original version unknown** and show local-versus-new differences without claiming they are proven user edits. Do not suppress file changes behind a skill count.

## Collect choices and review the final plan

For each locally changed or unrecognized whole skill, offer:

- **Keep my version** — leave the entire skill unchanged.
- **Use the new version** — back up reviewed local content, then update that skill's distributed files.

Keep conflicts by default when the user has not chosen. Store the explicit choices in the updater's decisions format using the generated report's per-unit review tokens; preserve those tokens and follow the documented schema rather than inventing it. A local report contains review data and must not be committed or uploaded.

Regenerate the preview with `--decisions <reviewed-decisions.json> --dry-run --report <final-review.json>`. Runtime updates depend on the chosen effective canonical skills: present any newly exposed runtime changes and obtain their choices too. Review one complete plan for canonical and runtime destinations before applying. Reuse unchanged exact choices/approval; changed source, files or tokens require a fresh preview, not a bypass.

## Apply and report

After the user approves the complete plan, apply with the same source/destination options plus `--decisions <reviewed-decisions.json> --yes`. Noninteractive apply requires the complete valid reviewed tokens; `--yes` alone never authorizes overwriting conflicts. Alternatively, the updater's graphical or terminal flow presents Keep/Use New choices, full diffs and one final confirmation.

Preserve unrelated skills, personal extra files and existing AGENTS.md content. Instruction integration is a separate explicit proposal. Never concatenate SKILL.md files, invent a merge, force-copy whole user folders, or update with `git pull`/reset. Private local files remain outside the distributed update.

Report the source revision when known, detected OS, updated/retained skills by destination, skipped or unknown items, and backup paths. Distinguish a preview from an applied update and report partial/nonzero outcomes honestly. Do not claim all skills were updated when some were kept. Commit, push or deploy only with explicit user intent; an update request alone does not authorize them.
