# Changelog

## Unreleased

### Added

- `wa-explain` for concise plain-language walkthroughs, short overviews and detailed follow-ups with intermediate data and worked examples, independently of the development pipeline.
- Automatic numbered install/update migrations with previews, ownership checks, complete backups, rollback and per-skill journals; the first migrates legacy runtime folders and installer records to `wa-*`.
- GitHub Copilot personal skills, target detection and CLI session-ledger hook setup, with explicit-only remote-server support.

### Improved

- Unified development intake by target language and risk, added a short workflow for clear low-risk changes, and connected existing UI/platform skills.
- Made focused local verification part of implementation, with requirements-derived behavior/edge-case tests and proportionate real-boundary evidence instead of tests that freeze internals.

- Added design reassessment before new variants: compare focused structural improvements with direct additions, explain maintenance trade-offs, and obtain scope approval for broader refactoring; architecture and review guidance carry the same check.

- Recorded maintainer verification of native Windows session-ledger operation and removed the obsolete unverified-Windows caveat.
- Namespaced all collection skills with `wa-`, including invocation names, runtime folders and update ownership records, so they coexist with other collections. Canonical file paths and recovery hooks remain stable; verified legacy folders migrate automatically and unknown folders are preserved for review.
- Strengthened reuse and placement checks in implementation and review, including searches for existing capabilities, suitable shared ownership, and explicit limits when repository context is unavailable.

### Internal

- Added a reusable pipeline scenario corpus and a disposable persistent-CLI fixture with an independent behavior oracle; agent trial evidence is recorded separately from helper/installer tests.

- Grouped collection helpers into installation, updates, migrations, hooks, skills and filesystem packages, with models beside their owners; public launch commands remain unchanged.

## 2026-11-12 — Automatic recovery and reviewed updates

### Added

- Session ledger with host-qualified identities, recovery by stable ID and native hooks installed automatically for Claude, Codex, Cursor and Antigravity.
- Generic, manually invoked remote-server skill using existing SSH configuration, with no embedded server details.
- Automatic recovery hook setup during installation, synchronization and updates, including upgrades of older collections; preview, status, removal and `--no-session-hooks` remain available.
- Recovery setup preserves unrelated settings, backs up changed configuration and rejects edited hooks or stale update reviews.
- Read-only standard-library Python structure checker with explicit file scope, JSON findings and regression tests.
- Thin repository instructions and a modular context index with architecture and development notes.
- Reviewed Python updater and chat entry skill, with original/local/new diffs, Keep/Use New choices, persistent backups and legacy-baseline handling.

### Improved

- Made repository context an explicit completion outcome across planning, implementation, delegated work and review, writing factual drafts for user review and retaining exact approval for active instructions and policies.
- Defined shared Python ownership rules for models and grouped dependency providers, direct imports and empty or documentation-only package initializers.
- Removed conflicting wildcard-import, initializer-export and app-startup wiring guidance, and replaced class-count rules with responsibility boundaries.
- Moved the installer's destination data model to its own models module and updated imports.
- Kept pipeline routers thin and loaded Python standards through their owning implementation reference at the relevant stage.
- Removed context size quotas while preserving topic ownership, important confirmed facts and user review.

### Fixed

- Reject ambiguous ledger bindings, unsafe storage paths, unverified Git exclusions and invalid session identities; preserve existing ignore files.
- Keep remote-server out of automatic discovery in unsupported runtime destinations during both install and reviewed updates.
- Kept private profiles/environment data and existing user instructions intact during reviewed updates; rejected stale decisions, overlapping destinations and unsafe report paths.
- Made installation additive: preserve conflicting skills, local edits/deletions, extra files and existing AGENTS.md; record hashes for safe managed updates and report conflicts accurately.
- Reject symlink-obstructed destinations and incomplete source scans instead of writing through links or reporting incomplete copies as successful.
- Require an explicit test runner for pollution tracing and distinguish clean, polluted and incomplete runs without deleting existing paths.
- Attribute trace samples and overlapping updates to the trigger process; reject stale recording stop markers and label sampled coverage as a heuristic.
- Restrict web design-system generation to suitable stacks, correct persisted page references, and adapt packaged checks to the shipped skill layout.

## 2026-10-22 — Installer portability

### Added

- Python-only installation from an extracted ZIP on Windows, macOS and Linux; Git is optional.
- Native launchers that locate Python, optional graphical checkboxes and a terminal selection fallback.
- Configuration, command and platform application detection, plus explicit targets for clean machines.
- A compatibility test matrix for Windows, macOS and Linux on Python 3.9 and 3.14.

### Improved

- Replaced the rsync-based implementation with staged standard-library file copies and rollback for failed replacements.
- Preserved destination-local review preferences when the canonical profile is absent.
- Added approved deployment-target, SDK and runtime selection rules to macOS design guidance.
- Documented Python's purpose, dependency-free copying and the remaining requirements of specialist skills.

### Removed

- Removed the redundant macOS skill AGENTS.md; SKILL.md remains the entry point with supporting references.

## 2026-10-22

### Added

- Initial Git repository containing 51 personal agent skills.
- English installation, synchronization, and usage documentation with a complete skill catalog.
- Repository context workflow for scoped work, selective documentation loading, and approval of persistent guidance changes.
- Read-only context discovery, local link checking, and file fingerprint utilities with 14 automated tests.

### Improved

- Integrated repository context into 26 existing skills and six supporting templates.
- Made domain glossary and architectural context changes explicit proposals instead of automatic writes.
- Added working-tree and supplied-diff inputs to review handoffs.
- Centralized canonical skills under `~/.wonsky-agents/skills/` and added runtime destination selection, including Antigravity support.

### Internal

- Excluded Python caches and the local personal reviewer-preferences profile from version control.
