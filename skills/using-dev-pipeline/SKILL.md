---
name: using-dev-pipeline
description: Use when starting any conversation about code, software, debugging, bugs, tests, architecture, planning, refactoring, reviews, quality, or completion checks. This is the bootstrap skill that routes to dev-pipeline or the correct specialist skill before any response, file inspection, implementation, debugging, review handling, or completion claim.
---

# Using Dev Pipeline

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed.

<SUBAGENT-STOP>
If you were dispatched as a subagent, skip routing again; retain the inherited scope/context packet and follow repository-context for your assigned targets.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a workflow skill might apply, you ABSOLUTELY MUST route first.
This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

This is the bootstrap skill for the local workflow system.

## Rule

Before taking any action or giving any substantive response, classify the request and route it.

If there is even a small chance a workflow skill applies, route first. Do not inspect files, propose fixes, or ask implementation questions before selecting the workflow.

If the request is about software work in any form, assume this skill applies unless there is a clear reason it does not.

## Do Not

- Jump into code
- Inspect files "just for a second"
- Propose fixes before choosing a workflow
- Answer workflow-relevant questions from memory instead of routing
- Ask clarifying questions that should happen inside the selected workflow
- Claim something is done without verification

## Red Flags

These thoughts mean you are about to bypass the workflow:

- "This is just a quick coding question"
- "I only need to peek at one file first"
- "I can answer this before choosing a route"
- "This sounds simple enough to skip the router"
- "The user did not explicitly ask for the pipeline"
- "I already know which fix to make"
- "Let me gather information first"
- "This doesn't need a formal skill"

If any of these thoughts appear, **route first**.

## Routing Table

| Request Type | Route |
|-------------|-------|
| New feature, refactor, architecture change, project planning (Python) | `dev-pipeline` |
| New feature, refactor, architecture, planning (Swift, C++, JS/TS, Go, Rust, any non-Python) | `unified-dev-pipeline` |
| Bug, test failure, unexpected behavior, integration issue | `systematic-debugging` first, then `dev-pipeline` if needed |
| Approved implementation plan, ready to build | `subagent-driven-development` or `executing-plans` |
| Multiple independent tasks or failures | `dispatching-parallel-agents` |
| Review your own work before merge or after a major task | `requesting-code-review` |
| Harsh / "thermo-nuclear" maintainability or code-quality review | `strict-code-quality-review` |
| Reviewing someone else's GitHub PR (post inline comments) | `pr-review-orchestrator` |
| Review feedback or PR comments received on your work | `receiving-code-review` |
| "Is this fixed?", "Does it pass?", "Are we done?" | `verification-before-completion` |
| Work is verified and user wants merge / PR / cleanup | `finishing-a-development-branch` |
| Changelog / version bump for shipped changes | `changelog-versioning` |
| Work summary / status update / "what did I do this week" | `git-report` |
| Pure testing / quality / audit request | `dev-pipeline` or `quality-gate` |
| Creative feature work, brainstorming ideas | `brainstorming` |

All skills live in `~/.wonsky-agents/skills/{skill-name}/SKILL.md`.

## Priority

1. User instructions
2. Specialist hard-gate skills (debugging, TDD, verification)
3. `dev-pipeline`
4. Ad hoc exploration or implementation

## Mandatory First Response Protocol

Before responding to ANY user message:

1. List available skills in your mind
2. Ask: "Does ANY skill match this request?"
3. If yes → Read the skill file and follow it
4. Announce which skill you're using
5. Follow the skill exactly

**Responding WITHOUT completing this checklist = automatic failure.**

## Skills with Checklists

Use the host's available plan/task-list tool for meaningful multi-step work; if none exists, keep a concise checklist in the conversation or working notes. TodoWrite is an example, not a required tool name. Group small related checks when every requirement remains accounted for. Never mark a task complete without its evidence; do not inflate a simple task into a checklist item per sentence.

## Announcing Skill Usage

Before using a skill, announce it:
"I'm using [Skill Name] to [what you're doing]."

## Notes

- `dev-pipeline` is the main entry point for **Python** delivery work; `unified-dev-pipeline` is the language-agnostic entry point for **any other language** (Swift, C++, JS/TS, Go, Rust, etc.). They share one core — `dev-pipeline` is just the Python skin.
- Debugging, review-feedback handling, and completion verification are separate hard-gate workflows.
- If there is any doubt whether a bug's root cause is known, route to `systematic-debugging`.
- If an implementation plan already exists, do not restart planning. Route into execution.
- If the request is software-related but does not cleanly match a specialist route, choose `dev-pipeline`.

## Common Rationalizations That Mean You're About To Fail

- "This is just a simple question" → Questions are tasks. Check for skills.
- "I can check git/files quickly" → Skills tell you HOW to gather information.
- "Let me gather information first" → Skills tell you HOW to gather information.
- "This doesn't need a formal skill" → If a skill exists for it, use it.
- "I remember this skill" → Skills evolve. Read the current version.
- "The skill is overkill for this" → Skills exist because simple things become complex.
- "I'll just do this one thing first" → Check for skills BEFORE doing anything.
- "Instructions were specific" → Specific instructions = clear requirements = when workflows matter MOST.

**If a skill for your task exists, you must use it or you will fail at your task.**
