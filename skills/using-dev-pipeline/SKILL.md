---
name: wa-using-dev-pipeline
description: Use when starting any conversation about code, software, debugging, bugs, tests, architecture, planning, refactoring, reviews, quality, or completion checks. This is the bootstrap skill that routes to wa-dev-pipeline or the correct specialist skill before any response, file inspection, implementation, debugging, review handling, or completion claim.
---

# Using Dev Pipeline

## Repository context preflight

Before repository work, read `~/.wonsky-agents/skills/repository-context/SKILL.md` and establish or refresh its scope/context packet. Reuse a valid packet within the same session; delegated agents must receive it and read the applicable guidance. Follow that skill's draft-first context workflow and exact approval gate for existing instructions or proposed policies. A context draft is not an active rule until reviewed. For multi-step repository work, use `~/.wonsky-agents/skills/session-ledger/SKILL.md`; reuse the current task's ledger and recover it after resume or compaction. Delegated workers receive relevant decisions and report updates to the parent.

<SUBAGENT-STOP>
If you were dispatched as a subagent, skip routing again; retain the inherited scope/context packet and follow wa-repository-context for your assigned targets.
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

## Routing

Read `~/.wonsky-agents/skills/unified-dev-pipeline/references/intake-routing.md` and use its authoritative table, target-language selection and short-workflow/escalation criteria. The selected skill owns the procedure. Do not keep a separate routing table here.

## Priority

1. User instructions
2. Specialist hard-gate skills (debugging, TDD, verification)
3. The target-language pipeline selected by the authoritative intake reference
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

- `wa-dev-pipeline` is the main entry point for **Python** delivery work; `wa-unified-dev-pipeline` is the language-agnostic entry point for **any other language** (Swift, C++, JS/TS, Go, Rust, etc.). They share one core — `wa-dev-pipeline` is just the Python skin.
- Debugging, review-feedback handling, and completion verification are separate hard-gate workflows.
- If there is any doubt whether a bug's root cause is known, route to `wa-systematic-debugging`.
- If an implementation plan already exists, do not restart planning. Route into execution.
- For software work without a better specialist route, use the authoritative intake reference to select the target-language pipeline; unresolved/mixed-language work stays in `wa-unified-dev-pipeline`.

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
