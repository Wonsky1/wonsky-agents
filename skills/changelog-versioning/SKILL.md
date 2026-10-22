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

### 1. Determine the Version Number

Follow [Semantic Versioning](https://semver.org/):

| Change type | Bump | Example |
|-------------|------|---------|
| Breaking API/behavior change | **MAJOR** | 1.0.0 → 2.0.0 |
| New feature, new endpoint, new UI section | **MINOR** | 1.0.0 → 1.1.0 |
| Bug fix, performance tweak, wording change | **PATCH** | 1.0.0 → 1.0.1 |

When in doubt, use **minor** for features, **patch** for fixes.

### 2. Classify Each Change

Every change goes into exactly one category:

**User-facing** (shown to end users on the frontend):
- `Added` — new capability or feature
- `Improved` — enhancement to existing functionality
- `Fixed` — bug fix
- `Removed` — removed capability

**Developer-only** (hidden from frontend, visible in the file):
- `Internal` — new endpoints, refactors, CI changes, config updates, dependency upgrades

### 3. Write the Entry

Add a new section at the **top** of `CHANGELOG.md`, below the file header:

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
- Date is today's date
- Only applicable category headers are present (omit empty ones)
- No duplicate information between user-facing and internal sections

## Frontend Behavior

The frontend strips `### Internal` sections automatically using a regex before rendering. Users only see `Added`, `Improved`, `Fixed`, and `Removed` entries. The file header (title + intro paragraph) is also stripped — rendering starts from the first `## [` heading.

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
