# Wonsky Agents

A personal collection of 52 agent skills, development workflows, and small utilities for Cursor, Claude Code, Codex, and Antigravity.

The canonical source is `~/.wonsky-agents/skills/`. New runtime skill directories receive copies including scripts, references, templates, and assets. Later synchronization preserves user changes and extra files. Edit the canonical files, then sync them.

## What's included

- **Development pipeline:** routing, planning, architecture, task decomposition, implementation, debugging, review, and verification.
- **Repository context:** explicit task/read/write scope, selective documentation loading, factual drafts written for user review, and approval before changing existing instructions or policies.
- **Specialist skills:** SwiftUI, macOS design, UI/UX, Obsidian, domain modeling, and more.
- **Installation and updates:** OS/runtime detection, destination selection, original/local/new comparisons, reviewed whole-skill choices and backups.

See the [complete skill catalog](docs/skills.md).

## Install on macOS, Linux or Windows

The installer requires **Python 3.9+ only**, using its standard library. No `rsync`, Bash, Git, package manager, administrator rights, virtual environment or `pip install` is needed. If Python is missing, install it from [python.org](https://www.python.org/downloads/) first; Python is not assumed to be bundled with a clean operating system.

Python provides the same file copying, runtime detection, path handling and selection logic on all three systems. It also runs the optional read-only repository-context helper. The skills themselves are Markdown; an agent can read them without Python. Some specialist skills have separate requirements, such as Xcode for building a Mac app or the Obsidian CLI for interacting with a vault.

### Without Git

1. Download the repository using **Code → Download ZIP** on [GitHub](https://github.com/Wonsky1/wonsky-agents).
2. Extract the ZIP and open a terminal in the extracted folder.
3. Run the appropriate command:

**macOS / Linux:**

```sh
python3 install.py
```

**Windows PowerShell / Command Prompt:**

```powershell
py -3 install.py
```

If your Python installation provides `python` instead of `py`, use `python install.py`.

The installer detects the operating system, offers destinations, and copies this collection into `~/.wonsky-agents/` before syncing the selected agent folders. On Windows, `~` means the current user's home, normally `%USERPROFILE%`. Cancelling selection writes nothing.

Optional native launchers find a suitable Python automatically: `sh install.sh` on macOS/Linux, or `.\install.ps1` in Windows PowerShell. If PowerShell blocks scripts, use `py -3 install.py` directly; changing the execution policy is unnecessary. The old `scripts/sync-skills.sh` entry point delegates to the Python implementation.

### With Git (optional)

```sh
git clone git@github.com:Wonsky1/wonsky-agents.git "$HOME/.wonsky-agents"
cd "$HOME/.wonsky-agents"
python3 install.py
```

On Windows, run `py -3 install.py` from the cloned folder. SSH cloning needs your existing GitHub SSH setup; ZIP installation does not.

An existing nonempty canonical folder requires `--update` when installing from another extracted download. This enables a preserving update, not forced replacement. Run the installer already inside the canonical folder for normal synchronization.

Cross-skill instructions use `~/.wonsky-agents/skills/`. `WONSKY_AGENTS_HOME` changes the install/sync root but does not rewrite those references, so the default location is recommended. `CODEX_HOME`, if set, controls the Codex destination.

This is a personal configuration. Some Obsidian skills include the owner's local vault path and should be adapted for another machine or user.

### Personal review preferences

`skills/github-pr-review/reviewer-preferences.md` is intentionally excluded from Git because the local profile contains personal review history. Before using that skill, copy your existing profile or create your own preferences in the canonical skill folder. Keep private repository names, review excerpts, and account details out of commits.

An existing destination profile is retained when the source lacks one. When both contain a profile, it follows the same managed-file checks as other files: a local edit is preserved and reported as a conflict. Store new learned preferences in the canonical private profile so synchronization can distribute approved changes.

## Choose and sync skills

Use `python3` below on macOS/Linux; on Windows use `py -3` or `python`.

```sh
python3 install.py --list
python3 install.py --dry-run
python3 install.py
```

The default selector shows real checkboxes when Python's optional Tk interface and a graphical session are available. No Tk installation is required: it falls back to a terminal list with `[x]` selections. Use `--terminal` to select that mode directly. In the terminal, enter numbers to toggle choices, then press Enter to install; `a` selects all, `n` clears selection, and `q` cancels. Detected destinations start selected.

Explicit selection also works on a clean machine, even before the agent creates a configuration folder:

```sh
python3 install.py --targets cursor,claude,codex,antigravity,agents
python3 install.py --all
python3 install.py --dry-run --targets codex
python3 install.py --sync-only --targets codex
```

`--all` selects only detected destinations. `--targets` may create skill folders for agents that are not detected; it does not install the agent applications. Unattended runs require `--targets` or `--all`. `--list` and `--dry-run` make no filesystem changes.

| Target | Default destination | Detection evidence |
|---|---|---|
| `cursor` | `~/.cursor/skills/` | Config directory, `cursor` command or known app location |
| `claude` | `~/.claude/skills/` | Config directory, `claude` command or known app location |
| `codex` | `~/.codex/skills/` | Config directory, `codex` command or known app location; honors `CODEX_HOME` |
| `antigravity` | `~/.gemini/config/skills/` | Config directory, `antigravity`/`agy` command or known app location |
| `agents` | `~/.agents/skills/` | Existing `.agents` directory |

Platform-specific detection checks macOS app bundles, typical Windows user/system application directories, and Linux XDG config/data directories and desktop entries. Detection is best effort; portable/custom installations may need explicit `--targets`. These are agent applications and configuration folders, not installed model weights. Antigravity's destination follows its [skills documentation](https://antigravity.google/docs/skills?app=antigravity-ide).

### Existing skills and instructions are preserved

- New skills are added alongside existing skills. Different-name skills, system skills and plugins are untouched.
- A same-name skill with conflicting content is skipped as a whole. Its local edits, extra assets and files remain intact; Markdown instructions are never blindly appended together.
- A private `.wonsky-state/` directory records hashes and original distributed file bytes installed or verified byte-identical by this installer. Private review profiles and environment files are not cached as original content. Later updates replace a recorded file only if it is still unchanged. Local edits and deletions block that skill update. Files no longer supplied by the collection are retained; synchronization does not prune old content.
- Existing `AGENTS.md` files are always preserved, including in a canonical-folder update and inside skills. Global instructions and instructions in other repositories are never edited. A new canonical installation may receive the collection's own instructions. Future instruction changes require review and approval separately.
- Destination symlinks and paths obstructed by symlinks are retained and reported as conflicts. Source skills must contain regular files and directories. Cache files are excluded from new copies.

The summary distinguishes added, updated, unchanged and conflicting skill folders. Exit 0 means no conflicts, 1 an error, and 2 preserved conflicts needing review. `--dry-run` reports the same checks without writing files or state. A staged copy protects each skill from copy failures; the complete multi-target installation is not one atomic transaction. Do not run concurrent installations into the same destination.

Older installations have no recorded ownership. A byte-identical old copy can be adopted safely. To update a known older copy, retain its previous extracted collection and supply it explicitly as a baseline:

```sh
python3 install.py --sync-only --targets codex --baseline /path/to/previous/wonsky-agents
```

Only files whose installed bytes match that trusted baseline qualify for an update; user edits still conflict. Without a baseline, differing same-name copies stay untouched. Review conflicts and merge the intended changes yourself; the installer has no force-overwrite option. Baseline folders are read only and need a `skills/` directory. A canonical ZIP update uses `--update --baseline /path/to/previous/wonsky-agents` under the same checks.

Multiple discovery roots can produce duplicate entries in an agent that reads both `~/.agents/skills/` and its own skills directory; choose the destinations you need. Existing local `~/.cursor/sync-skills.sh` wrappers still delegate to the compatible entry point; a fresh install does not create a Cursor wrapper.

## Version-aware macOS guidance

`macos-design-guidelines` selects advice using the app's minimum deployment target, build SDK/Xcode and runtime OS. The host OS alone does not determine which APIs the app may use. The skill includes API milestones for macOS 11–12, 13, 14–15, 26 and a documentation/SDK check for 27 and later, with availability checks and working fallbacks. It is not rewritten during installation, so a Linux or Windows agent can still work on a Mac project. Native build/runtime verification requires the corresponding macOS tools or CI.

## Use the development workflow

Start with `using-dev-pipeline`, then select `dev-pipeline` for Python or `unified-dev-pipeline` for other languages. The pipeline routes to the relevant specialist skills. Use the host application's skill invocation syntax or ask the agent to read the corresponding `SKILL.md`.

Repository work uses `repository-context` to establish scope and load relevant instructions and documents. The agent writes missing factual context and useful factual updates as concrete drafts, then explicitly asks the user to review correctness and completeness. Existing accurate coverage needs no artificial update. Outcomes distinguish reviewed updates, verified-current coverage, drafts awaiting review, instruction changes awaiting approval and declined changes. A task plan or chat summary does not substitute for repository documentation.

Root `AGENTS.md` stays short and points to the context index. Topic files include the useful confirmed requirements, responsibilities, patterns, boundaries, reasons and integration details needed for future work; there is no fixed word or paragraph limit. They reuse existing documentation and exclude repeated prose, speculation and task diaries. This repository's [context index](docs/agent-context/index.md) follows that structure.

Existing user instructions and proposed active policies require exact approval before edits. Draft facts do not become instruction authority merely because they were written. Installation and updating preserve existing AGENTS.md and never bootstrap other repositories. See [repository-context](skills/repository-context/SKILL.md) and its [templates](skills/repository-context/references/templates.md).

These workflows guide agent behavior. They do not enforce filesystem permissions or guarantee compliance by every model.

### Python structure checks

The shared [Python structure contract](skills/implementation-guide/references/python-structure.md) assigns data declarations to `models/`, provider/assembly concerns to focused `dependencies/` modules, and behavior to its owning modules. Package initializers are empty or package documentation only; imports come from defining modules with no wildcard imports. Existing published package APIs require an authorized migration before breaking callers. These rules apply to planning, delegated implementation and review.

The standard-library checker handles mechanical violations without importing or executing target code:

```sh
python3 -B skills/implementation-guide/scripts/check_structure.py --repo-root . install.py scripts
python3 -B -m unittest discover -s skills/implementation-guide/scripts/tests -v
```

Pass explicit Python files or directories within the declared repository/read scope, including changed initializers and untracked source. It reports JSON file/line/rule/message findings: wildcard imports, executable initializer content, recognizable misplaced models and narrow import-resolved dependency construction in router/app files. Exit codes are 0 for no findings, 1 for violations and 2 for an incomplete check (input/read/parse failure). Directory symlinks are not traversed and escapes are rejected. Unrecognized declarations, resource lifecycle and semantic cohesion still need review; a clean scan is not proof of sound architecture. The checker never rewrites code or context documents.

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
python3 -B -m unittest discover -s tests -v
```

These checks cover the context helper, installer, updater and selected diagnostic tools, not every specialist tool. The installer suite uses temporary homes, including a full install followed by sync with an empty PATH (no Git or rsync). Detection branches for all three platforms are tested with fixtures. The GitHub Actions matrix is configured to run the installer suite on real Windows, macOS and Linux runners with Python 3.9 and 3.14; adding a workflow does not mean those remote jobs have already passed. Context-helper symlink tests run on Unix runners.

## Update with review

Ask an agent **“Update Wonsky Agents”** to use the [wonsky-agents-update skill](skills/wonsky-agents-update/SKILL.md), or run from the canonical folder:

```sh
python3 update.py
```

On Windows use `py -3 update.py` or `python update.py`. The updater needs Python 3.9+ standard library only. It checks the OS, offers detected agent destinations, and downloads GitHub `main` at one pinned commit into temporary staging. It does not execute downloaded code, require Git, reset a checkout or push anything. The archive strategy follows [GitHub's source archive guidance](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives).

The graphical review uses optional Tk; `--terminal` selects equivalent terminal prompts. Before changing installed files, it shows every affected canonical/runtime skill and file, original-to-local edits, original-to-offered changes and the effect of replacement. Binary files show hashes/sizes. Private profiles and environment-file contents are omitted and preserved. Choose for each locally changed skill:

- **Keep my version:** leave that whole skill unchanged, including newly offered files. Keeping a canonical skill skips its runtime update too.
- **Use the new version:** back up current content and state, then replace the reviewed distributed files. Personal extras and every existing AGENTS.md remain. Removal of an obsolete owned file is included in the preview; unrelated files are never pruned.

One final confirmation covers the resulting canonical and runtime plan. Changes during review invalidate the affected approval. Backups remain under `~/.wonsky-agents/.wonsky-backups/`; their manifests identify the destination and saved state. Updates are atomic per file with rollback for a failed unit, not one transaction across all destinations; earlier successful units remain applied if a later unit fails. Do not run concurrent updates into the same installation.

### Preview or use a downloaded collection

```sh
python3 update.py --dry-run --targets codex --report /outside-installation/review.json
python3 update.py --from /path/to/new-extracted/wonsky-agents --terminal
python3 update.py --from /path/to/new-extracted/wonsky-agents \
  --baseline /path/to/trusted-previous/wonsky-agents --targets codex
```

`--dry-run` may download/extract temporary source data; installed files and ownership state are unchanged. Unresolved choices default to Keep. Exit codes are 0 for an applied/previewed plan with no kept units, 1 for an error, 2 when units are kept, and 130 for cancellation by interrupt. Keeping a skill is an intentional partial outcome, not an assertion that every skill updated.

Old installations may have hashes but no original bytes, or no ownership record at all. The updater recovers verified originals from its cache or an explicit trusted `--baseline`. If this is impossible, it says **Original version unknown** and shows local-versus-new differences rather than inventing the user's exact edits. A same-name skill alone does not prove ownership. Future accepted installations retain their original distributed content for accurate comparisons. Runtime copies are never silently merged into the canonical source.

**If the old installation has no `update.py`:** download/extract a new ZIP, then run its `update.py --from /path/to/that/extracted/folder`. It reviews the existing canonical installation before replacing anything. `install.py --update` remains a conservative compatibility path: it keeps conflicts rather than offering replacement; use `update.py` for the complete review flow.

For a Git checkout, reviewed file updates preserve `.git` and do not move `HEAD`, commit or push. The applied file changes appear in the working tree; use your normal Git workflow explicitly when desired.

### Agent-assisted reviewed choices

The JSON report contains every plan and its `choices` mapping. Each choice has a `token` tied to the reviewed source hashes, local file fingerprints and installation state. Keep its version, source revision, unit IDs and tokens intact; change only `choice` to `keep`, `update` (unmodified units) or `replace` (explicitly approved local edits). Store this local review data outside installation/skill directories and version control.

```sh
python3 update.py --dry-run --targets codex --report /outside-installation/review.json
# Inspect the diffs and choose Keep/Use New through the agent or interactive UI.
python3 update.py --dry-run --targets codex --decisions /outside-installation/review.json \
  --report /outside-installation/final-review.json
python3 update.py --targets codex --decisions /outside-installation/final-review.json --yes
```

If changing a canonical choice exposes new runtime plans, review those plans and choices before apply. Applying a decisions file requires complete matching tokens for the exact resulting plan; stale or incomplete choices are rejected. `--yes` by itself only applies safe updates and keeps conflicts; it is never a blanket overwrite option. Reports are never written over unrelated user files or instructions. Use the same source and destination arguments across review/apply. If GitHub `main` changes meanwhile, create a new preview.

## Layout

```text
skills/<name>/SKILL.md       Skill entry points
skills/<name>/references/    Supporting guidance, where needed
skills/<name>/scripts/       Helpers and tests, where needed
install.py                  Conservative installer and sync entry point
update.py                   Reviewed updater with diffs, choices and backups
install.sh / install.ps1     Optional native Python launchers
scripts/                    Detection, file state, review, acquisition and copying
tests/                      Installer/updater checks using temporary homes
.github/workflows/          Windows, macOS and Linux compatibility checks
docs/skills.md              Skill catalog
CHANGELOG.md                Collection changes
```

## Sources and licensing

This collection combines locally maintained workflow instructions with adapted or imported skills and reference data. Existing source references and metadata remain in the individual skill folders. The repository does not assign a blanket license to third-party material. The repository-context design was informed by the scope and handoff patterns in [khc/dotagents](https://github.com/khc/dotagents); its helper was implemented locally.
