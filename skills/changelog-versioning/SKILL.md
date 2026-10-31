---
name: changelog-versioning
description: Create and update changelog entries when implementing features, fixes, or improvements. Use when shipping user-visible changes, completing a feature branch, cutting a release, or when the user asks to update the changelog or version.
---

# Changelog Versioning

Guide for creating consistent, well-formatted changelog entries that separate user-facing changes from internal/technical details.

## When to Use

- After implementing a feature, fix, or improvement
- When the user asks to bump the version or update the changelog
- Before merging a feature branch or creating a PR
- When completing a batch of related changes

## Process

### 1. Read the release contract

Inspect the existing changelog, version source and release workflow. Keep an established Unreleased section and category/date conventions. Do not assign a new release number or date merely because implementation finished; bump only when the user requested release/version work. If the project uses Semantic Versioning, use this mapping:

| Change type | Bump | Example |
|-------------|------|---------|
| Breaking API/behavior change | **MAJOR** | 1.0.0 → 2.0.0 |
| New feature, new endpoint, new UI section | **MINOR** | 1.0.0 → 1.1.0 |
| Bug fix, performance tweak, wording change | **PATCH** | 1.0.0 → 1.0.1 |

When in doubt, use **minor** for features, **patch** for fixes.

### 2. Classify Each Change

Every change goes into exactly one category:

**User-facing** (intended for end users):
- `Added` — new capability or feature
- `Improved` — enhancement to existing functionality
- `Fixed` — bug fix
- `Removed` — removed capability

**Developer-focused** (visibility depends on the actual publishing/rendering pipeline):
- `Internal` — new endpoints, refactors, CI changes, config updates, dependency upgrades

### 3. Write the Entry

Follow the existing format. Add to Unreleased when that is the project convention; for an authorized release, create the dated version section in the established position:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- User-friendly description of what's new

### Fixed
- User-friendly description of what was fixed

### Internal
- Technical detail only developers need to know
```

### 4. Writing Guidelines

**User-facing entries:**
- Write from the user's perspective — what changed for them
- Use plain language, no jargon
- One line per change, concise
- Good: "Dashboard load time improved by 60%"
- Bad: "Added Redis caching layer for KPI snapshot queries"

**Internal entries:**
- Include technical specifics: endpoints, libraries, config
- Good: "Backend `GET /api/changelog` endpoint serving CHANGELOG.md"
- Good: "Migrated scheduled jobs from APScheduler to asyncio-native scheduler"

### 5. Verify

- Entry is at the top (newest first)
- Release date/version matches the authorized release; Unreleased remains undated when that is the established format
- Only applicable category headers are present (omit empty ones)
- No duplicate information between user-facing and internal sections

## Frontend Behavior

Do not assume Internal sections or headers are hidden. Inspect the real renderer/publishing workflow before promising visibility behavior. If no such renderer exists, treat the entire changelog as readable by its audience and omit private or sensitive details.

## Example

```markdown
## [1.5.0] - 2026-04-10

### Added
- Comparative analytics — side-by-side period comparison for any KPI
- Natural language alert rules — describe conditions in plain English

### Improved
- Incident search now supports fuzzy matching for misspelled terms

### Internal
- Alert rule NLP parser using structured output with JSON schema validation
- Upgraded `langchain` to v0.3
```
