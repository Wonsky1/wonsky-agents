---
name: obsidian-template-create
description: Create Obsidian notes from existing vault templates correctly. Use when the user asks to create a note, page, record, restaurant, person note, daily note, product note, category note, or any vault item from an Obsidian template.
---

# Obsidian Template Create

Use Obsidian's template system as the source of truth. Do not manually recreate template bodies.

## Required Checks

Before creating the note:

1. Confirm the current vault is the intended vault.
   The intended vault must come from the skill, explicit user instruction, or a verified CLI target, not from the current workspace by assumption.
   For this user, default to `/Users/vlad/Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault` unless explicitly overridden.
2. Confirm the target template actually exists in that vault.
3. Inspect one existing note of the same type or the configured destination folder when possible.
4. Identify which fields are present in the template versus which values must come from the user.
5. Build one concise list of all meaningful missing values that cannot be inferred from the request, attachments, or existing note context.

If the template cannot be found, stop treating the request as a template flow. Either switch to `obsidian-markdown` with explicit user confirmation on the schema, or ask only for the missing required fields.

If the template exists but meaningful user-provided fields are still missing, ask for them before considering the note complete. Do not silently leave fields like `store`, `price`, `buy_again`, ratings, or free-text impressions blank unless the user explicitly requested a draft or placeholder-only creation.

## Workflow

1. List templates with `obsidian templates` if the template name is not obvious.
2. Read the chosen template with `obsidian template:read name="<template name>"` when available, or inspect the underlying template file.
3. Determine the destination folder from existing notes, vault config, or explicit user instruction.
4. If meaningful values are missing, ask for them in one concise batch before finalizing.
5. Create the note with `obsidian create path="<vault-relative-path>" template="<template name>"`.
6. Read the created file.
7. Edit only placeholders and item-specific content.
8. Verify the large template body was not rewritten by comparing against `obsidian template:read name="<template name>"` when practical.

## Per-template Notes

Short template-specific instructions live in this skill folder under `templates/*.md`.

Read only the matching file when creating that template. Keep these notes tiny so they do not pollute context.

Current files:

- `templates/restaurant.md`: Restaurant template notes

## Defaults

- Prefer vault-relative paths for CLI commands.
- Use direct file edits only after Obsidian has created the note from the template.
- If the CLI is unavailable, copy the exact template file first, then edit placeholders only.
- Never invent template fields, frontmatter keys, or destination folders when the vault can be inspected first.
- Never silently ship a template-created note with meaningful blank user fields unless the user explicitly accepted a draft.
