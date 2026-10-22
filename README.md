# Wonsky Agents

A personal collection of 51 agent skills, development workflows, and small utilities for Cursor, Claude Code, Codex, and Antigravity.

The canonical source is `~/.wonsky-agents/skills/`. Runtime skill directories receive full copies, including scripts, references, templates, and assets. Edit the canonical files, then sync them.

## What's included

- **Development pipeline:** routing, planning, architecture, task decomposition, implementation, debugging, review, and verification.
- **Repository context:** explicit task/read/write scope, selective documentation loading, and approval before changing persistent repository guidance.
- **Specialist skills:** SwiftUI, macOS design, UI/UX, Obsidian, domain modeling, and more.
- **Sync utility:** detection of supported local runtimes and destination selection.

See the [complete skill catalog](docs/skills.md).

## Install

Requirements: Git, Bash, and `rsync`. Python 3.9+ is required for the repository-context helper. Other skills may need their own tools; consult the relevant `SKILL.md` before use.

```sh
git clone git@github.com:Wonsky1/wonsky-agents.git "$HOME/.wonsky-agents"
cd "$HOME/.wonsky-agents"
```

The default location matters: cross-skill references use `~/.wonsky-agents/skills/`. The `WONSKY_AGENTS_HOME` environment variable changes the sync source, but does not rewrite those references.

If `~/.wonsky-agents` already exists, keep it and inspect its Git status/remotes before cloning or pulling. Do not overwrite an existing installation.

This is a personal configuration, not a universal preset. Some Obsidian skills include the owner's local vault path and should be adapted for another machine or user.

### Personal review preferences

`skills/github-pr-review/reviewer-preferences.md` is intentionally excluded from Git because the local profile contains personal review history. The `github-pr-review` skill expects this file: copy your existing profile or create your own local preferences before using that skill. Keep private repository names, review excerpts, and account details out of commits.

Restore this local file before syncing on a new machine if your destination already has a profile you want to retain. Sync replaces matching skill-directory contents, including files absent from the canonical copy.

## Sync skills

Preview detected destinations:

```sh
./scripts/sync-skills.sh --dry-run
```

Choose destinations interactively:

```sh
./scripts/sync-skills.sh
```

In a macOS terminal with `osascript` available, this opens a multiple-selection list. Otherwise it prompts for destination numbers in the terminal. The macOS list uses multiple selection, not literal checkbox controls.

Sync every detected destination, or choose explicit targets:

```sh
./scripts/sync-skills.sh --all
./scripts/sync-skills.sh --targets cursor,claude,codex,agents
./scripts/sync-skills.sh --dry-run --targets codex
```

| Target | Destination | Detection |
|---|---|---|
| `cursor` | `~/.cursor/skills/` | `.cursor` directory or Cursor app |
| `claude` | `~/.claude/skills/` | `.claude` directory or Claude app |
| `codex` | `~/.codex/skills/` | `.codex` directory or Codex app |
| `antigravity` | `~/.gemini/config/skills/` | `.gemini/config` directory or Antigravity app |
| `agents` | `~/.agents/skills/` | `.agents` directory |

Detection uses known configuration directories and macOS application locations; it is not a scan for installed model weights or every possible agent application. An explicit target must currently be detected. Antigravity's destination follows its [skills documentation](https://antigravity.google/docs/skills?app=antigravity-ide).

Sync uses `rsync --delete` **inside each matching skill directory**. Canonical content replaces destination edits. It does not remove unrelated skill directories or sync application-managed plugins and system skills. Copies in multiple discovery roots may appear as duplicate skill entries in a host that reads both roots; choose only the destinations you need.

The previous local entry point `~/.cursor/sync-skills.sh`, where already installed, delegates to this script. A fresh clone does not install that compatibility wrapper.

## Use the development workflow

Start with `using-dev-pipeline`, then select `dev-pipeline` for Python or `unified-dev-pipeline` for other languages. The pipeline routes to the relevant specialist skills. Use the host application's skill invocation syntax or ask the agent to read the corresponding `SKILL.md`.

Repository work uses `repository-context` to establish scope and load applicable instructions and documents. It can propose a small root `AGENTS.md` and a modular `docs/agent-context/index.md`, while reusing existing README files, glossaries, and ADRs.

Persistent repository guidance changes require a concrete proposal and user approval. Installation does not create or rewrite instructions in other repositories. See [repository-context](skills/repository-context/SKILL.md) and its [templates](skills/repository-context/references/templates.md).

These workflows guide agent behavior. They do not enforce filesystem permissions or guarantee compliance by every model.

## Repository-context utilities

```sh
python3 skills/repository-context/scripts/context_tools.py discover /path/to/repository/src
python3 skills/repository-context/scripts/context_tools.py check-links \
  /path/to/repository/docs/agent-context/index.md --repo-root /path/to/repository
python3 skills/repository-context/scripts/context_tools.py fingerprint /path/to/repository/AGENTS.md
```

For a non-Git tree, supply `--repo-root` to `discover`. The commands are read-only. Discovery reports candidates, not instructions already read by an agent. Link checking handles common local Markdown links; it does not crawl linked documents or validate heading anchors.

Run the helper's automated checks:

```sh
python3 -B -m unittest discover -s skills/repository-context/scripts/tests -v
bash -n scripts/sync-skills.sh
```

These checks cover the context helper and shell syntax, not every skill or external tool in this collection.

## Update

```sh
cd "$HOME/.wonsky-agents"
git status
git pull --ff-only
./scripts/sync-skills.sh
```

Resolve local edits deliberately before pulling. Runtime copies are not merged back into the canonical source automatically.

## Layout

```text
skills/<name>/SKILL.md       Skill entry points
skills/<name>/references/    Supporting guidance, where needed
skills/<name>/scripts/       Helpers and tests, where needed
scripts/sync-skills.sh       Runtime detection and synchronization
docs/skills.md              Skill catalog
CHANGELOG.md                Collection changes
```

## Sources and licensing

This collection combines locally maintained workflow instructions with adapted or imported skills and reference data. Existing source references and metadata remain in the individual skill folders. The repository does not assign a blanket license to third-party material. The repository-context design was informed by the scope and handoff patterns in [khc/dotagents](https://github.com/khc/dotagents); its helper was implemented locally.
