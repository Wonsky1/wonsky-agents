---
name: obsidian-template-update
description: Update concise per-template instructions for Obsidian template creation. Use when the user says a previous template-created note was wrong, explains a correction, or asks to remember how a specific Obsidian template should be filled next time.
---

# Obsidian Template Update

Update the matching short instruction file used by `obsidian-template-create`.

## Workflow

1. Identify the template affected by the user's feedback.
2. Open `/Users/vlad/.codex/skills/obsidian-template-create/templates/<template>.md`.
3. Add or revise only the minimal rule needed to prevent the mistake.
4. Keep the file concise: prefer one-line bullets, remove stale or redundant wording.
5. Do not copy full templates, large examples, or long explanations into the instruction file.

## Naming

Use lowercase template slugs:

- Restaurant template -> `restaurant.md`
- Daily template -> `daily.md`
- Person note template -> `person-note.md`
- Category template -> `category.md`
- Product template -> `product.md`
