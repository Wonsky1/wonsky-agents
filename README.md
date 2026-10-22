# Wonsky Agents

A personal collection of 51 agent skills, development workflows, and small utilities for Cursor, Claude Code, Codex, and Antigravity.

The canonical source is `~/.wonsky-agents/skills/`. Runtime skill directories receive full copies, including scripts, references, templates, and assets. Edit the canonical files, then sync them.

## What's included

- **Development pipeline:** routing, planning, architecture, task decomposition, implementation, debugging, review, and verification.
- **Repository context:** explicit task/read/write scope, selective documentation loading, and approval before changing persistent repository guidance.
- **Specialist skills:** SwiftUI, macOS design, UI/UX, Obsidian, domain modeling, and more.
- **Sync utility:** detection of supported local runtimes and destination selection.

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

An existing nonempty canonical folder is not overwritten by a different extracted download unless you pass `--update`. Run the installer already inside the canonical folder for normal synchronization.

Cross-skill instructions use `~/.wonsky-agents/skills/`. `WONSKY_AGENTS_HOME` changes the install/sync root but does not rewrite those references, so the default location is recommended. `CODEX_HOME`, if set, controls the Codex destination.

This is a personal configuration. Some Obsidian skills include the owner's local vault path and should be adapted for another machine or user.

### Personal review preferences

`skills/github-pr-review/reviewer-preferences.md` is intentionally excluded from Git because the local profile contains personal review history. Before using that skill, copy your existing profile or create your own preferences in the canonical skill folder. Keep private repository names, review excerpts, and account details out of commits.

When a downloaded collection lacks that profile, installation and synchronization retain an existing destination profile. When the canonical source contains a profile, its version replaces the runtime copy.

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

Each matching skill directory is prepared as a complete copy, then replaces the previous directory. Destination-only files inside that skill are removed, except the local review profile described above. Unrelated skill directories, application-managed plugins and system skills are retained. Cache files are excluded. A skill-directory symlink is safely replaced by a regular directory without modifying its former target. Source skills must use regular files/directories, making installation independent of Windows symlink privileges. A failed copy retains the old skill; installation is not an atomic transaction across all selected skills and destinations.

Multiple discovery roots can produce duplicate entries in an agent that reads both `~/.agents/skills/` and its own skills directory; choose the destinations you need. Existing local `~/.cursor/sync-skills.sh` wrappers still delegate to the compatible entry point; a fresh install does not create a Cursor wrapper.

## Version-aware macOS guidance

`macos-design-guidelines` selects advice using the app's minimum deployment target, build SDK/Xcode and runtime OS. The host OS alone does not determine which APIs the app may use. The skill includes API milestones for macOS 11–12, 13, 14–15, 26 and a documentation/SDK check for 27 and later, with availability checks and working fallbacks. It is not rewritten during installation, so a Linux or Windows agent can still work on a Mac project. Native build/runtime verification requires the corresponding macOS tools or CI.

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
python3 -B -m unittest discover -s tests -v
```

These checks cover the context helper and installer, not every specialist tool. The installer suite uses temporary homes, including a full install followed by sync with an empty PATH (no Git or rsync). Detection branches for all three platforms are tested with fixtures. The GitHub Actions matrix is configured to run the installer suite on real Windows, macOS and Linux runners with Python 3.9 and 3.14; adding a workflow does not mean those remote jobs have already passed. Context-helper symlink tests run on Unix runners.

## Update

For a Git checkout, review local changes, pull, then sync:

```sh
cd "$HOME/.wonsky-agents"
git status
git pull --ff-only
python3 install.py
```

For a ZIP installation, download and extract the new ZIP, then run from that extracted folder:

```sh
python3 install.py --update
```

Use `py -3` on Windows. `--update` replaces collection files and matching canonical skill contents from the download; private review preferences and unrelated skill directories are retained. It does not merge competing local edits. Review or back up local customizations before updating. Runtime copies are not merged into the canonical source automatically.

## Layout

```text
skills/<name>/SKILL.md       Skill entry points
skills/<name>/references/    Supporting guidance, where needed
skills/<name>/scripts/       Helpers and tests, where needed
install.py                  Cross-platform installer and sync entry point
install.sh / install.ps1     Optional native Python launchers
scripts/                    Detection, copying, selection and compatibility wrapper
tests/                      Installer checks using temporary homes
.github/workflows/          Windows, macOS and Linux compatibility checks
docs/skills.md              Skill catalog
CHANGELOG.md                Collection changes
```

## Sources and licensing

This collection combines locally maintained workflow instructions with adapted or imported skills and reference data. Existing source references and metadata remain in the individual skill folders. The repository does not assign a blanket license to third-party material. The repository-context design was informed by the scope and handoff patterns in [khc/dotagents](https://github.com/khc/dotagents); its helper was implemented locally.
