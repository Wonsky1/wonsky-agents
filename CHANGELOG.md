# Changelog

## Unreleased

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
