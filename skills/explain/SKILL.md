---
name: wa-explain
description: Use when the user asks how a system, service, code path or technical concept works, wants a plain-language walkthrough, or asks to unpack one step with concrete examples.
---

# Explain through one example

Help the reader follow what happens, using simple words and small, concrete examples. More depth means showing more of the mechanism while keeping the language simple.

## Scope and mode

This is an independent explanation skill, outside the development pipeline. Explaining does not authorize implementation, refactoring, repository edits or starting a development workflow. Respect the user's language, requested format and length.

| User intent | Response |
|---|---|
| "Briefly", "high level", "коротко" | A short overview of the purpose and main parts. |
| "How does our service work?", "поясни як працює" | Default: follow one concrete input from entry to result. |
| "How exactly?", "more about step 4", "детальніше" | Expand only the selected mechanism, with intermediate data and a worked example. |

Infer the mode from the request; do not make the user choose a level before answering. An experienced reader can want an overview, and a beginner can want detail. A direct request for a different format takes precedence over the default walkthrough.

## Ground the explanation

For an actual project, read its applicable instructions and relevant documentation, then trace the real entry point, important calls, configuration and prompts. Inspect only what is needed for the requested path. Use available read-only tools; do not run services or external requests merely to illustrate them.

- Use verified endpoint names, payload fields, branches, defaults and prompt locations. Distinguish configured defaults from known runtime overrides.
- Link to a few relevant source files, with verified line numbers when useful. Link directly to an important prompt when it is available. Never invent a file link.
- If implementation or runtime evidence is missing, say precisely what is unknown. A general illustration may still help, but label it as such rather than presenting it as the user's system.
- Label invented requests, results, token IDs, vectors and scores as illustrative. Do not expose credentials or private customer data in examples.
- Preserve technical accuracy when simplifying. For example, check which similarity or distance metric is actually used, which direction is better, and which pooling method the model uses; do not borrow these from a generic RAG example.

## Default walkthrough

Start with one sentence about what the system does. Choose one representative input, preferably the user's own example, and keep following it throughout the answer.

Use a short numbered sequence, usually about 5–8 steps for a service. Combine minor operations; do not inventory every function. Each step should make clear:

1. What arrives here.
2. What this part does and why.
3. What it passes onward.

Show small payloads, a couple of returned fragments or a sample output where they make the transition easier to understand. At a decision, briefly explain the relevant alternatives and why this input follows this branch. End with the result the user receives.

Keep each step to a few short sentences plus any useful example. Explain a new term in one sentence when it first appears. Prefer ordinary verbs to abstract descriptions. Use bold for the important input or result; keep JSON and code valid rather than inserting bold markers inside code blocks.

## Expand a selected step

Keep the original example and explain only the part the user asked about. Show **before → operation → after**, including intermediate values when saying "we transform it" would hide the mechanism.

- For data transformations, show the small input structure, the operation on it, and the resulting structure.
- For a matrix, label what rows and columns represent. Use a few rows and dimensions; explicitly mark omitted or simplified data.
- For calculations, work through enough actual numbers to reproduce the result. Check the arithmetic. Do not just name the operation or show its final output.
- Keep identifiers, counts and dimensions distinct: token ID 910 does not mean there are 910 tokens or rows.
- Do not assign made-up human meanings to individual vector coordinates or treat an illustrative score as a guaranteed semantic match.

Read [the worked examples](references/examples.md) when shaping a walkthrough or explaining a transformation. They demonstrate presentation, not facts about the user's architecture or model.

Use a small table, code block or diagram only when it makes the mechanism easier to follow. A specialist skill can help with a genuinely needed source or visualization task when available; no orchestrator, plugin or subagent is required for an ordinary explanation.

## Before responding

- Does the reader follow one concrete example all the way through the requested scope?
- Are important transformations visible, with readable intermediate data?
- Are project facts supported, illustrative data labeled, and links real?
- Is the answer short enough for the request, with unfamiliar terms explained?
- On a follow-up, did the answer deepen the selected step instead of repeating the whole service?
