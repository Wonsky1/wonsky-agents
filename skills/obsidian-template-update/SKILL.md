---
name: obsidian-template-update
description: Update concise per-template instructions for Obsidian template creation. Use when the user says a previous template-created note was wrong, explains a correction, or asks to remember how a specific Obsidian template should be filled next time.
---

# Obsidian Template Update

Update the matching short instruction file used by `obsidian-template-create`.

## Workflow

1. Identify the template affected by the user's feedback.
2. Resolve the canonical collection from `WONSKY_AGENTS_HOME`, or `~/.wonsky-agents` when unset. Read `<canonical-root>/skills/obsidian-template-create/templates/<template>.md`. If that collection is unavailable, establish its actual source with the user before a persistent write; a runtime copy is not an upstream source.
3. Propose the exact path and minimal diff needed to prevent the mistake. Follow `repository-context`'s approval gate for lasting instructions; a general correction is not approval of unspecified text. Reuse an applicable explicit standing instruction or approval of this exact diff rather than asking twice.
4. Apply only the approved change in the canonical file. Keep it concise: prefer one-line bullets and remove stale or redundant wording only when that removal was approved.
5. Do not copy full templates, large examples, or long explanations into the instruction file. Synchronize approved canonical changes through the installer; report any preserved installation conflicts instead of editing mirrors independently.

## Naming

Use lowercase template slugs:

- Restaurant template -> `restaurant.md`
- Daily template -> `daily.md`
- Person note template -> `person-note.md`
- Category template -> `category.md`
- Product template -> `product.md`
