---
name: prompt-engineering
description: Use when writing prompts for LLMs, designing system prompts, creating agent instructions, skill descriptions, or any AI interaction that needs reliable, high-quality outputs. Covers foundational techniques (zero-shot, few-shot, CoT), advanced frameworks (ToT, ReAct, self-consistency), and practical patterns for production use.
---

# Prompt Engineering

Systematic discipline for designing inputs that produce reliable, high-quality LLM outputs. This is not artisanal prompt-writing — it is specification engineering applied to language models.

## Core Principle

**Write clearer specs, not longer prompts.** A well-structured 10-line prompt outperforms a rambling 50-line prompt. Every token should earn its place.

## When to Use

- Writing system prompts for agents or tools
- Creating skill descriptions or instructions
- Designing prompts for data extraction, analysis, or generation
- Troubleshooting prompts that produce inconsistent results
- Building prompt templates for repeatable workflows

## The Four Pillars

Based on the comprehensive taxonomy (Sahoo et al., 2025):

| Pillar | What It Covers | Key Techniques |
|--------|---------------|----------------|
| **Instruction** | Role, task, constraints, format | System prompt design, TCOF structure |
| **Knowledge** | Context the model needs | Few-shot examples, retrieval-augmented context |
| **Reasoning** | How the model should think | Chain-of-Thought, Tree-of-Thought, ReAct |
| **Reliability** | Consistent, verifiable outputs | Self-consistency, structured output, verification |

## Foundational Techniques

### Zero-Shot Prompting

Direct instruction without examples. Works for straightforward tasks.

```
Classify the following customer message as: complaint, question, feedback, or request.

Message: "I've been waiting 3 weeks for my order and nobody will respond to my emails."

Classification:
```

**When to use:** Simple, well-defined tasks where the model already understands the format.
**Limitation:** Unreliable for nuanced format/style requirements.

### Few-Shot Prompting

Provide 3-5 examples demonstrating exact desired behavior. The single most reliable technique for controlling output format and style.

```
Extract the action items from meeting notes.

Example 1:
Notes: "We agreed to launch the beta next Tuesday. Maria will prepare the deploy checklist."
Action items:
- Maria: Prepare deploy checklist (by Tuesday)
- Team: Launch beta (Tuesday)

Example 2:
Notes: "The API rate limit needs to increase. Jake will file the infra ticket today."
Action items:
- Jake: File infra ticket for API rate limit increase (today)

Now extract:
Notes: "{{input}}"
Action items:
```

**Rules for examples:**
- Show the exact format you want — examples beat adjectives
- Include at least one edge case (empty input, ambiguous case)
- Keep examples diverse but representative
- 3-5 examples is the sweet spot; more rarely helps

### Chain-of-Thought (CoT)

The model reasons step-by-step before answering. Proven by Wei et al. (2022) to improve reasoning accuracy dramatically — from 17.7% to 78.7% on GSM8K math benchmarks with PaLM 540B.

**Zero-shot CoT** — add a single instruction:
```
Q: A store has 45 apples. They sell 3/5 of them and receive a shipment of 20 more. How many apples do they have?

Think through this step by step, then give the final answer.
```

**Few-shot CoT** — show reasoning in examples:
```
Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?
A: Roger started with 5 balls. 2 cans of 3 tennis balls each is 6 tennis balls. 5 + 6 = 11. The answer is 11.

Q: {{new_question}}
A:
```

**Key findings from the CoT paper:**
- Only effective at scale (100B+ parameters) — small models produce fluent but illogical chains
- Bigger gains on harder problems; minimal effect on trivial single-step tasks
- Reasoning must come BEFORE the answer (not after) to be effective
- Robust across different annotators and exemplar styles
- Natural language steps outperform equation-only or variable-compute approaches

**When to use:** Multi-step reasoning, math, logic, complex analysis, debugging.

### Self-Consistency

Run the same CoT prompt multiple times with sampling, then take the majority answer. Improves CoT by 12-18% on benchmarks.

**When to use:** High-stakes decisions where you can afford multiple calls. Particularly effective for math and logic problems.

## Advanced Frameworks

### Tree-of-Thought (ToT)

Extends CoT from a linear chain to a tree of reasoning paths. The model explores multiple approaches, evaluates each, and backtracks when a path fails.

```
Consider this problem: {{problem}}

Generate 3 different approaches to solve this:

Approach 1: [describe]
Evaluation: [strengths and weaknesses]

Approach 2: [describe]
Evaluation: [strengths and weaknesses]

Approach 3: [describe]
Evaluation: [strengths and weaknesses]

Best approach and why: [select and justify]
Final solution using the best approach: [solve]
```

**When to use:** Problems with multiple valid solution paths, creative tasks, strategic decisions.

### ReAct (Reasoning + Acting)

Combines reasoning with tool use through thought-action-observation loops. This is the foundation of most AI agent frameworks.

```
Thought: I need to find the current stock price of AAPL to answer this question.
Action: search("AAPL stock price today")
Observation: AAPL is trading at $187.50 as of market close.
Thought: Now I can calculate the portfolio value.
Action: calculate(500 * 187.50)
Observation: 93750
Thought: The portfolio is worth $93,750.
Answer: Your 500 shares of AAPL are worth $93,750.
```

**When to use:** Tasks requiring external data, tool use, or multi-step actions with real-world interaction.

### Prompt Chaining

Break complex tasks into a sequence of simpler prompts, where each output feeds the next.

```
Step 1: Extract key entities from the document → entities
Step 2: For each entity, determine relationships → graph
Step 3: Summarize the relationship graph → summary
```

**When to use:** Complex multi-part tasks, pipelines, when you need intermediate validation.

## Practical Patterns

### The TCOF Structure

Organize every prompt into four sections:

```
**Task:** What you want done (one clear sentence)
**Context:** Background the model needs (domain, audience, constraints)
**Output:** Exact format specification (JSON schema, template, bullet structure)
**Format:** Tone, length, style requirements
```

### System Prompt Template

For agents and tools:

```
## Role
You are a [specific role] specializing in [domain].

## Goal
[One sentence: what success looks like]

## Constraints
- [Specific limitation 1]
- [Specific limitation 2]
- [What you must NOT do]

## Output Format
[Exact structure: JSON schema, markdown template, etc.]

## Verification
Before responding, verify:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
```

### XML Tags for Structure (Claude-Specific)

Claude responds well to XML tags for separating sections:

```xml
<instructions>
Analyze the code for security vulnerabilities.
</instructions>

<code>
{{user_code}}
</code>

<output_format>
For each vulnerability found:
- **Location:** file:line
- **Severity:** Critical/High/Medium/Low
- **Description:** What's wrong
- **Fix:** How to fix it
</output_format>
```

### Negative Constraints

Tell the model what NOT to do — often more effective than positive instructions:

```
Do NOT:
- Make up information not present in the source
- Use technical jargon the audience wouldn't understand
- Provide medical/legal/financial advice
- Include personal opinions as facts
```

### Output Anchoring

Start the model's response to steer format:

```
Analyze this data and respond in the following JSON format:

```json
{
  "summary":
```

The model will continue the JSON structure naturally.

## Production Patterns

Patterns proven in real production systems.

### Structured CoT (Domain-Specific Thinking)

Instead of generic "think step by step," give the model a **predefined reasoning framework** specific to your domain. Far more reliable than freeform thinking.

```xml
<thinking>
  1. **Technical Core Analysis**: [Extract logic and substance from source data.]
  2. **Strategic Mapping**: [Plan 5-7 high-density sections covering the full scope.]
  3. **Beautification Plan**: [Identify UI elements for bolding, variables for backticks.]
  4. **Anchor Matching**: [Map references to logical prose blocks.]
  5. **Visual Selection**: [Select max 8 critical visual markers.]
</thinking>
<output>[Final deliverable here]</output>
```

**Why this works:** The model follows your reasoning path instead of inventing its own. Each numbered step is a checkpoint — if the model skips one, you see it immediately.

**Template:**
```xml
<thinking>
  1. **[Analysis step]**: [What to extract or understand.]
  2. **[Planning step]**: [How to structure the response.]
  3. **[Verification step]**: [What to check before outputting.]
</thinking>
<output>[Deliverable]</output>
```

### Constraint Severity Tagging

Not all constraints are equal. Tag them with severity so the model knows what's non-negotiable vs nice-to-have:

```xml
<constraints_checklist>
  - [CRITICAL] **Substance over Style**: Deep technical detail required.
  - [CRITICAL] **Max 8 images per document**: Do not exceed.
  - [UX] Full timeline coverage: End should be as detailed as beginning.
  - [UX] NO horizontal rules `---`. Use clean headers.
</constraints_checklist>
```

`[CRITICAL]` items are hard gates. `[UX]` items are quality improvements. The model prioritizes accordingly.

### XML Prompt Architecture (Full System Prompt)

For complex production prompts, use XML tags to create an unambiguous, parseable structure:

```xml
<system_prompt>
  <role_definition>
    You are [specific role] specializing in [domain].
  </role_definition>

  <formatting_specifications>
    [Detailed format rules with examples]
  </formatting_specifications>

  <response_format>
    <thinking>[Structured reasoning steps]</thinking>
    <output>[Complete example of desired output]</output>
  </response_format>
</system_prompt>
```

**Pair system + user prompts:**
```xml
<!-- System: defines WHO and HOW -->
<system_prompt>
  <role_definition>...</role_definition>
  <formatting_specifications>...</formatting_specifications>
</system_prompt>

<!-- User: defines WHAT with data -->
<mission_request>
  <objective>[What to produce]</objective>
  <source_data>
    <input_a>{variable_a}</input_a>
    <input_b>{variable_b}</input_b>
  </source_data>
  <constraints_checklist>[Prioritized rules]</constraints_checklist>
</mission_request>
```

### Prompt Templating for Pipelines

Production systems use **template variables** for repeatable, testable prompts:

```python
PROMPT = """
<mission_request>
  <objective>Synthesize the data into a technical report.</objective>
  <source_data>
    <raw_input>{user_input}</raw_input>
    <context>{rag_context}</context>
  </source_data>
</mission_request>
"""
```

**Rules for production templates:**
- Keep prompts in dedicated files (e.g., `prompts/generation.py`), not inline
- Use `{variable}` or `{{variable}}` placeholders — never string concatenation
- Version prompts alongside code — prompt changes are behavior changes
- Test prompts with representative inputs before deploying

### Surgical Revision Prompts

When editing existing outputs, prevent the model from rewriting everything:

```xml
<revision_protocol>
  1. MINIMAL INTERVENTION: Edit only requested parts.
  2. STYLE MATCHING: Maintain the existing format and conventions.
  3. CONTINUITY: Follow existing numbering and naming sequences.
</revision_protocol>

<final_check_commands>
  - Did I implement ALL feedback items?
  - Did I preserve the parts that were NOT mentioned in the feedback?
  - Is the output structurally identical except for the requested changes?
</final_check_commands>
```

### Self-Verification Gates

End prompts with explicit self-check questions the model must answer before outputting:

```xml
<final_check_commands>
  - Did I address every item in the requirements?
  - Is the output in the correct format?
  - Did I violate any constraint from the checklist?
  - Are all references/citations accurate?
</final_check_commands>
```

This is more effective than "check your work" because it gives the model **specific things to verify**.

## Quality Checklist

Before deploying any prompt:

- [ ] **Task is clear** — could a human follow these instructions unambiguously?
- [ ] **Success criteria defined** — what does "good output" look like, specifically?
- [ ] **Format specified** — exact structure, not "well-formatted"
- [ ] **Constraints explicit** — what to avoid, length limits, scope boundaries
- [ ] **Examples included** — at least 1-3 when format matters
- [ ] **Edge cases covered** — what happens with empty/weird/ambiguous input?
- [ ] **Verification built in** — how does the model check its own work?
- [ ] **Tested with variations** — different inputs produce consistently good outputs?

## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| "Write a good summary" | "Good" is subjective | Specify length, audience, key points to include |
| Wall of text instructions | Model loses focus | Use sections, headers, bullet points |
| Vague role assignment | "You are helpful" means nothing | "You are a senior Python developer reviewing for security" |
| No output format | Inconsistent structure | Provide JSON schema, template, or example |
| Too many constraints | Contradictory rules | Prioritize: must-have vs nice-to-have |
| Examples without diversity | Model overfits to pattern | Include edge cases and variations |
| Reasoning after answer | CoT doesn't help | Reasoning must precede the final answer |
| Prompt too long | Dilutes key instructions | Front-load critical instructions, trim fluff |

## Model-Specific Notes

| Model Family | Optimization |
|-------------|-------------|
| **Claude** | XML tags for structure, concise focused prompts, explain WHY constraints matter |
| **GPT** | Detailed instructions, numeric constraints, system/user message separation |
| **Gemini** | Section markers, structured formatting, clear delimiters |
| **Open-source** | More explicit formatting, stronger examples, simpler instruction chains |

## Iteration Strategy

When a prompt isn't working:

1. **Diagnose** — Is the output wrong in format, content, or both?
2. **Add an example** — Show exactly what you want (most common fix)
3. **Add a constraint** — Tell it what NOT to do (for unwanted content)
4. **Restructure** — Move critical instructions to the beginning
5. **Simplify** — Remove unnecessary context that may confuse
6. **Chain** — Break into smaller prompts if too complex for one

**The 80/20 rule:** Most prompt problems are fixed by (1) adding an example, (2) specifying format, or (3) being more specific about what you want. Advanced techniques are rarely needed.

## References

- Wei et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." NeurIPS 2022. arXiv:2201.11903
- Wang et al. (2022). "Self-Consistency Improves Chain of Thought Reasoning in Language Models."
- Yao et al. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models."
- Yao et al. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models."
- Sahoo et al. (2025). "A Comprehensive Taxonomy of Prompt Engineering Techniques." Frontiers of Computer Science.
- Anthropic (2025). "Prompting Best Practices." Claude API Documentation.
