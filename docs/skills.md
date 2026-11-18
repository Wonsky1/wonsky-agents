# Skill catalog

This collection contains 55 skills. Each entry links to the canonical instructions and any supporting resources. Invocation and discovery depend on the host application.

| Skill | Purpose |
|---|---|
| [wa-remote-server](../skills/remote-server/SKILL.md) | Manually invoked SSH work on a user-selected server; excluded from hosts without verified manual-only discovery. |
| [wa-session-ledger](../skills/session-ledger/SKILL.md) | Compact task decisions, verification evidence, running jobs and pending items with explicit identity recovery. |
| [wa-batch-grill-me](../skills/batch-grill-me/SKILL.md) | A relentless interview that asks every frontier question at once, round by round. |
| [wa-brainstorming](../skills/brainstorming/SKILL.md) | Use when creating or developing, before writing code or implementation plans - refines rough ideas into fully-formed designs through collaborative questioning, alternative exploration, and incremental validation. |
| [wa-changelog-versioning](../skills/changelog-versioning/SKILL.md) | Create and update changelog entries when implementing features, fixes, or improvements. |
| [wa-condition-based-waiting](../skills/condition-based-waiting/SKILL.md) | Use when tests have race conditions, timing dependencies, or inconsistent pass/fail behavior - replaces arbitrary timeouts with condition polling to wait for actual state changes, reducing timing-related flakes. |
| [wa-defense-in-depth](../skills/defense-in-depth/SKILL.md) | Use when invalid data causes failures deep in execution, requiring validation at multiple system layers - validates relevant responsibility and trust boundaries to reduce bypasses and improve diagnostics. |
| [wa-defuddle](../skills/defuddle/SKILL.md) | Extract clean markdown content from web pages using Defuddle CLI, removing clutter and navigation to save tokens. |
| [wa-dev-pipeline](../skills/dev-pipeline/SKILL.md) | Preferred entry point for nearly all Python software engineering work. |
| [wa-dispatching-parallel-agents](../skills/dispatching-parallel-agents/SKILL.md) | Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies - dispatches multiple agents to investigate and fix independent problems concurrently. |
| [wa-domain-modeling](../skills/domain-modeling/SKILL.md) | Build and sharpen a project's domain model. |
| [wa-executing-plans](../skills/executing-plans/SKILL.md) | Use when you have an approved implementation plan to execute sequentially with checkpoints - loads plan, reviews critically, executes tasks in batches, reports for review between batches. |
| [wa-explain](../skills/explain/SKILL.md) | Explain systems and technical concepts in simple words through one concrete example; expand selected steps with intermediate data and worked calculations. |
| [wa-find-skills](../skills/find-skills/SKILL.md) | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. |
| [wa-finishing-a-development-branch](../skills/finishing-a-development-branch/SKILL.md) | Use after work is verified and the user wants options for merge, PR, branch retention, or cleanup - guides completion by presenting structured options and handling chosen workflow. |
| [wa-git-report](../skills/git-report/SKILL.md) | Generate a management-ready summary of work from git history. |
| [wa-github-pr-review](../skills/github-pr-review/SKILL.md) | Draft and post approved GitHub PR review comments using the GitHub MCP server (preferred) or gh fallback - creates pending reviews, batches comments, chooses event types, applies reviewer-preferences, and learns from corrections. |
| [wa-grill-me](../skills/grill-me/SKILL.md) | A relentless interview to sharpen a plan or design. |
| [wa-grill-with-docs](../skills/grill-with-docs/SKILL.md) | A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go. |
| [wa-grilling](../skills/grilling/SKILL.md) | Grill the user relentlessly about a plan, decision, or idea. |
| [wa-implementation-guide](../skills/implementation-guide/SKILL.md) | Guides production-quality code implementation following SOLID principles, clean architecture, and project conventions. |
| [wa-json-canvas](../skills/json-canvas/SKILL.md) | Create and edit JSON Canvas files (.canvas) with nodes, edges, groups, and connections. |
| [wa-macos-design-guidelines](../skills/macos-design-guidelines/SKILL.md) | Apple Human Interface Guidelines for Mac. |
| [wa-obsidian](../skills/obsidian/SKILL.md) | Universal entrypoint for Obsidian work. |
| [wa-obsidian-bases](../skills/obsidian-bases/SKILL.md) | Create and edit Obsidian Bases (.base files) with views, filters, formulas, and summaries. |
| [wa-obsidian-cli](../skills/obsidian-cli/SKILL.md) | Interact with Obsidian vaults using the Obsidian CLI to read, create, search, and manage notes, tasks, properties, and more. |
| [wa-obsidian-markdown](../skills/obsidian-markdown/SKILL.md) | Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, and other Obsidian-specific syntax. |
| [wa-obsidian-template-create](../skills/obsidian-template-create/SKILL.md) | Create Obsidian notes from existing vault templates correctly. |
| [wa-obsidian-template-update](../skills/obsidian-template-update/SKILL.md) | Update concise per-template instructions for Obsidian template creation. |
| [wa-pr-review-orchestrator](../skills/pr-review-orchestrator/SKILL.md) | Use when reviewing a GitHub PR end-to-end, posting PR comments, or when the user asks for a PR review - first runs the strict thermo-nuclear maintainability review over the full diff, then uses the GitHub PR review workflow only for approved comments. |
| [wa-prompt-engineering](../skills/prompt-engineering/SKILL.md) | Use when writing prompts for LLMs, designing system prompts, creating agent instructions, skill descriptions, or any AI interaction that needs reliable, high-quality outputs. |
| [wa-quality-gate](../skills/quality-gate/SKILL.md) | Comprehensive quality assurance — tests, security audit, performance review, and documentation. |
| [wa-receiving-code-review](../skills/receiving-code-review/SKILL.md) | Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation. |
| [wa-repository-context](../skills/repository-context/SKILL.md) | Use before repository planning, implementation, debugging or review; when handing work to another agent; or when proposing changes to AGENTS.md, repository rules, context, domain glossaries or architecture decisions. |
| [wa-requesting-code-review](../skills/requesting-code-review/SKILL.md) | Use after completing a major task, batch of implementation work, complex bug fix, or before merge to verify work meets requirements - dispatches reviewer subagent to review implementation against plan or requirements. |
| [wa-root-cause-tracing](../skills/root-cause-tracing/SKILL.md) | Use when errors occur deep in execution and you need to trace back to find the original trigger - systematically traces bugs backward through call stack, adding instrumentation when needed, to identify source of invalid data or incorrect behavior. |
| [wa-solution-architect](../skills/solution-architect/SKILL.md) | Designs technical architecture for features and services. |
| [wa-strategic-planner](../skills/strategic-planner/SKILL.md) | C-level strategic planning for new features, changes, or improvements. |
| [wa-strict-code-quality-review](../skills/strict-code-quality-review/SKILL.md) | Use when the user asks for a thermo-nuclear, thermonuclear, harsh, deep maintainability, architecture, abstraction, spaghetti-code, large-file, or code quality review - applies an unusually strict structural quality bar. |
| [wa-subagent-driven-development](../skills/subagent-driven-development/SKILL.md) | Use when an approved implementation plan exists and tasks can be executed task-by-task with delegated implementation and review - dispatches fresh subagent per task with code review between tasks for fast iteration with quality gates. |
| [wa-swiftui-expert-skill](../skills/swiftui-expert-skill/SKILL.md) | Use when writing, reviewing, or refactoring SwiftUI code for iOS or macOS, including state and `@Observable` data flow, view composition, resizable layouts, safe areas, display scale, performance, lists, environment, localization, animation, Liquid Glass,… |
| [wa-systematic-debugging](../skills/systematic-debugging/SKILL.md) | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes - four-phase framework (root cause investigation, pattern analysis, hypothesis testing, implementation) that ensures understanding before attempting solutions. |
| [wa-task-decomposer](../skills/task-decomposer/SKILL.md) | Breaks an architecture proposal into ordered, atomic implementation tasks with file-level specificity, dependency graphs, and test criteria. |
| [wa-template-slide-from-screenshot](../skills/template-slide-from-screenshot/SKILL.md) | Match a screenshot in a python-pptx WBR/QBR generator after verifying the project adapter applies. |
| [wa-test-driven-development](../skills/test-driven-development/SKILL.md) | Use when implementing any feature or bugfix, before writing implementation code - write the test first, watch it fail, write minimal code to pass; ensures tests actually verify behavior by requiring failure first. |
| [wa-testing-anti-patterns](../skills/testing-anti-patterns/SKILL.md) | Use when writing or changing tests, adding mocks, or tempted to add test-only methods to production code - prevents testing mock behavior, production pollution with test-only methods, and mocking without understanding dependencies. |
| [wa-testing-pytest](../skills/testing-pytest/SKILL.md) | Creates pytest unit tests for changed files. |
| [wa-ui-ux-pro-max](../skills/ui-ux-pro-max/SKILL.md) | UI/UX design intelligence for web, mobile, and desktop. |
| [wa-unified-dev-pipeline](../skills/unified-dev-pipeline/SKILL.md) | Language-agnostic entry point for nearly all software engineering work in ANY language (Swift, C++, Python, JS/TS, Go, Rust, etc.). |
| [wa-using-dev-pipeline](../skills/using-dev-pipeline/SKILL.md) | Use when starting any conversation about code, software, debugging, bugs, tests, architecture, planning, refactoring, reviews, quality, or completion checks. |
| [wa-using-git-worktrees](../skills/using-git-worktrees/SKILL.md) | Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification. |
| [wa-verification-before-completion](../skills/verification-before-completion/SKILL.md) | Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always. |
| [wa-wonsky-agents-update](../skills/wonsky-agents-update/SKILL.md) | Review and update Wonsky Agents with exact local diffs, whole-skill Keep/Use New choices, backups and preserved user instructions. |
| [wa-writing-plans](../skills/writing-plans/SKILL.md) | Use when design is complete and you need detailed implementation tasks for engineers with zero codebase context - creates comprehensive implementation plans with exact file paths, complete code examples, and verification steps assuming engineer has minimal… |
| [wa-writing-skills](../skills/writing-skills/SKILL.md) | Use when creating new skills, editing existing skills, or verifying skills work before deployment - applies TDD to process documentation by testing with subagents before writing, iterating until bulletproof against rationalization. |
