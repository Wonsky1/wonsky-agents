---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment - applies TDD to process documentation by testing with subagents before writing, using bounded scenarios to check correct behavior, limits and instruction precedence.
---

# Writing Skills

## Overview

Agent skills are concise, enforceable process documents for Cursor and similar agents. This meta-skill treats **writing skills as TDD applied to documentation**: define failing scenarios first, write the minimum skill text that passes, then refactor for clarity. Compliance is not the only success case: verify legitimate user overrides, inapplicable rules and preservation of user work.

## When to Use

- Creating a new skill.
- Editing an existing skill for clarity, scope, or enforcement.
- Verifying a skill works (e.g. with a subagent) before relying on it in production or sharing it.

## What Is a Skill?

A skill captures **reusable** techniques, patterns, tools, or reference material. It is **not** a one-off narrative ("how we fixed ticket #123") or a brain dump without triggers and boundaries.

## Where Skills Live

| Scope | Typical path |
|-------|----------------|
| Personal | `~/.wonsky-agents/skills/` |
| Project | `.cursor/skills/` |
| This pipeline | `~/.wonsky-agents/skills/<skill-name>/SKILL.md` |

Cross-references should use full paths such as `~/.wonsky-agents/skills/{skill-name}/SKILL.md` so agents resolve them consistently.

## TDD Mapping for Skills

| TDD concept | Skill equivalent |
|-------------|------------------|
| Test case | Pressure scenario (how an agent/user will try to skip or misuse the skill) |
| Failing test | Scenario where current docs allow wrong behavior |
| Production code | The `SKILL.md` body (rules, checklists, red flags) |
| Refactor | Tighten wording, split sections, add cross-refs without changing behavior |
| Regression | Re-run pressure scenarios after edits |

## When to Create / Don't Create

**Create** when the same decision procedure, checklist, or pattern repeats across tasks and mistakes are costly.

**Don't create** when a single inline comment suffices, when the "skill" is app-specific business logic, or when it duplicates an existing skill with only cosmetic differences.

## Skill Types

| Type | Purpose | Example focus |
|------|---------|----------------|
| **Technique** | How to execute a procedure | Steps, verification gates |
| **Pattern** | When to choose what | Decision tables, trade-offs |
| **Reference** | Lookup material | Tables, links, one canonical example |

## Directory Structure

- **`SKILL.md` required** at the skill root (e.g. `my-skill/SKILL.md`).
- Supporting files optional (`references/`, `scripts/`, `assets/`).
- **Flat namespace per folder:** one skill per directory; name directory after the skill slug.

## SKILL.md Structure

1. **YAML frontmatter:** `name` + `description` (required).
2. **Sections** (use as appropriate; omit empty):
   - **Overview**
   - **When to Use**
   - **Core Pattern** (or Core Principle)
   - **Quick Reference** (table)
   - **Implementation** (steps, commands, integration)
   - **Common Mistakes**
   - **Real-World Impact** (why this matters)

## Description and Discovery

The `description` field is how agents decide which skills to load. Make it answer: **"Should I read this skill right now?"**

**Format:** Start with `"Use when..."` to focus on triggering conditions, then explain what the skill does.

**Content rules:**

- Use **concrete triggers, symptoms, and situations** -- not abstract categories
- Describe the **problem** (race conditions, inconsistent behavior) not language-specific symptoms (setTimeout, sleep)
- Write in **third person** (description is injected into system prompts)
- Stay **under ~500 characters**
- Avoid vague words ("sometimes", "maybe") unless paired with a decision rule

```yaml
# BAD: Too abstract, doesn't say when to use
description: For async testing

# BAD: Technology-specific when skill isn't
description: Use when tests use setTimeout/sleep and are flaky

# GOOD: Problem-oriented, includes when + what
description: Use when tests have race conditions, timing dependencies, or pass/fail inconsistently - replaces arbitrary timeouts with condition polling for reliable async tests
```

**Keyword coverage:** Use words an agent would search for -- error messages, symptoms ("flaky", "hanging", "pollution"), synonyms ("timeout/hang/freeze"), and tool names.

## Token Efficiency

- Target **tight** word counts: prefer tables and bullets over prose.
- **Progressive disclosure:** overview + quick reference first; deep detail in Implementation or linked files.
- **Cross-references:** point to `~/.wonsky-agents/skills/{skill}/SKILL.md` or project paths; do not rely on force-load semantics -- state the requirement in text ("read X before Y").
- **Move heavy details to supporting files** when reference material exceeds ~100 lines.
- **Don't repeat** what cross-referenced skills already cover.

## Naming Conventions

- **Active voice**, **verb-first** or **gerund-for-process** names: `using-git-worktrees`, `finishing-a-development-branch`, `writing-skills`.
- Match the `name` in frontmatter to the folder name.
- Name by **what you do** or the **core insight**: `condition-based-waiting` > `async-test-helpers`; `root-cause-tracing` > `debugging-techniques`.

## Cross-Referencing

- Cite **skill name + path** and **requirement markers** ("MUST read ... before ...").
- No assumption that another skill auto-loads; the reader (human or agent) follows explicit paths.

## Code Examples

**One excellent, minimal example beats many mediocre ones.** Show the happy path and one non-obvious edge case if needed.

## The Iron Law

Identify the reported failure and a bounded set of representative scenarios before changing instructions. Reuse reproduced audit evidence as the baseline instead of rerunning the same failing scenario for ceremony. Evaluate the revised text where scenario execution is requested and permitted; otherwise disclose the evaluation limit.

## Testing All Skill Types

| Type | Test focus |
|------|------------|
| Discipline-enforcing | Agent tries to skip gates -- skill must block in text ("never", "MUST stop") |
| Technique | Omit a step -- outcome should be clearly wrong per skill |
| Pattern | Wrong branch of a decision table -- skill should name the correct branch |
| Reference | Wrong lookup -- skill should point to the canonical table/section |

## RED-GREEN-REFACTOR for Skills

### RED: Baseline Testing (Watch It Fail)

Run test scenarios **without** the skill. Document exact agent behavior and rationalizations.

1. **Create pressure scenarios** -- combine 3+ pressures for discipline-enforcing skills.
2. **Run without skill** -- give the agent a realistic task with pressures present.
3. **Document choices and rationalizations** word-for-word.
4. **Identify patterns** -- which excuses appear repeatedly?

**Pressure types to combine:**

| Pressure | Example |
|----------|---------|
| **Time** | Emergency, deadline, deploy window closing |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior says skip it, manager overrides |
| **Economic** | Job, promotion, company survival at stake |
| **Exhaustion** | End of day, already tired, want to go home |
| **Social** | Looking dogmatic, seeming inflexible |
| **Pragmatic** | "Being pragmatic vs dogmatic" |

**Best tests combine 3+ pressures.** Single-pressure scenarios are too easy to resist.

**Key elements of good pressure scenarios:**

1. **Concrete options** -- Force A/B/C choice, not open-ended
2. **Real constraints** -- Specific times, actual consequences
3. **Real file paths** -- `/tmp/payment-system` not "a project"
4. **Make agent act** -- "What do you do?" not "What should you do?"
5. **No easy outs** -- Can't defer to "I'd ask the user" without choosing

### GREEN: Write Minimal Skill

Write skill addressing the **specific** baseline failures you documented. Don't add extra content for hypothetical cases -- write just enough to address actual observed failures.

Run the same scenarios with the skill, plus at least one legitimate user/host override or out-of-scope case. The agent should apply the rule only when appropriate.

If agent still fails: skill is unclear or incomplete. Revise and re-test.

### REFACTOR: Correct the specific failure

When a scenario fails, first check whether the rule was applicable, authorized and correct. A user override, conflicting higher-priority instruction or preservation of existing work can make noncompliance the right outcome. Fix a wrong or disproportionate rule instead of escalating its prohibitions.

Add only the wording needed for an observed ambiguity or missing boundary. Keep examples and counters tied to evidence. Use a bounded evaluation pass over the affected scenario families; report remaining uncertainty rather than iterating until no imaginable objection remains. No finite scenario set proves a skill “bulletproof.”

### Evaluation evidence

Record the scenario, expected decision, observed result and relevant source version. Cover normal use, the reported failure and a valid exception. Check clarity and discovery separately from whether the agent cited the rule. Reuse unchanged evidence; rerun affected cases after material edits when authorized.

## Skill Creation Checklist

**RED phase**

- [ ] Pressure scenarios documented (3+ combined pressures for discipline skills)
- [ ] Scenarios run WITHOUT skill; failures and rationalizations captured verbatim
- [ ] Patterns in rationalizations identified

**GREEN phase**

- [ ] Frontmatter valid (`name`, `description`)
- [ ] Description starts with "Use when..." with concrete triggers
- [ ] When to Use + Core Pattern present
- [ ] Quick Reference or equivalent
- [ ] Scenarios run WITH skill; agent now complies

**REFACTOR phase**

- [ ] New rationalizations identified from testing
- [ ] Explicit counters added for each loophole
- [ ] Rationalization table built from all iterations
- [ ] Red flags list created
- [ ] Affected scenarios checked, including valid override/out-of-scope cases; limits reported
- [ ] Meta-tested to verify clarity

**Quality checks**

- [ ] Description under length budget; triggers concrete; keywords present
- [ ] Small flowchart only if decision non-obvious
- [ ] No narrative storytelling; no multi-language code dilution

**Deployment**

- [ ] Path documented for consumers (`~/.cursor/...` or project)
- [ ] Changelog or commit message if versioned with code

## Common Rationalizations for Skipping Testing

| Excuse | Reality |
|--------|---------|
| "Skill is obviously clear" | Clear to you != clear to other agents. Test it. |
| "It's just a reference" | References can have gaps. Test retrieval. |
| "The change looks obvious" | Inspect the reported failure and relevant scenarios; state what was actually evaluated. |
| "I'll test if problems emerge" | Problems = agents can't use skill. Test BEFORE deploying. |
| "I'm confident it's good" | Confidence alone is not behavioral evidence; use scoped results and disclose limits. |
| "No time to test" | Deploying untested skill wastes more time fixing it later. |

## Discovery Workflow

How agents find your skill:

1. Encounter problem -> search for existing skill.
2. **Scan Overview + When to Use.**
3. Read **Core Pattern** / tables.
4. Load **one** full example or Implementation section when executing.

**Optimize for this flow** -- put searchable terms early and often.

Edit the canonical collection under `~/.wonsky-agents/skills/`; runtime mirrors are generated outputs. Other collections follow their declared source and approval boundaries. Exact persistent-guidance changes require repository-context approval before writes.

## Flowchart Conventions

When skills include Graphviz flowcharts, follow the conventions in `graphviz-conventions.dot` (bundled in this skill's directory):

| Shape | Meaning |
|-------|---------|
| Diamond | Decision / question (label ends with `?`) |
| Box | Action (label starts with verb) |
| Plaintext | Shell command (literal) |
| Ellipse | State (describes situation) |
| Octagon (red fill) | Warning / STOP |
| Double circle | Entry / exit point |

Edge labels: `yes` / `no` for binary decisions, descriptive conditions for multiple choices, `triggers` (dotted) for cross-process links.
