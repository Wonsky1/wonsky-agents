---
name: obsidian
description: Universal entrypoint for Obsidian work. Use when the user is working in an Obsidian vault and does not care which specialized Obsidian skill to choose. Prefer the obsidian CLI whenever it can do the task cheaply. Route to obsidian-template-create for creating notes from templates, obsidian-template-update for remembering concise template corrections, obsidian-cli for vault search/read/create/append/property/task/app/plugin/theme operations, obsidian-markdown for Obsidian markdown editing, obsidian-bases for .base files, json-canvas for .canvas files, and defuddle for web-page-to-markdown imports.
---

# Obsidian Router

Use this as the default skill for Obsidian-related requests when the right specialized skill is not explicitly named.

## Vault Source Of Truth

For this user, the default Obsidian vault path is:

`/Users/vlad/Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault`

Treat this iCloud Drive vault as the default authoritative target unless the user explicitly overrides it or a more specific referenced skill instruction says otherwise.

The target vault must come from an explicit source of truth:

1. a vault path or vault name written in the skill or its referenced instructions,
2. an explicit user instruction in the current conversation, or
3. a verified Obsidian CLI target selected from the running app.

Do not infer the vault from the current workspace alone when the skill or user specifies a different source of truth. In this setup, prefer the iCloud Drive vault above over the current workspace by default. If the vault is ambiguous, stop and clarify before creating or editing notes.

## Purpose

This skill is a small router. Do not duplicate the full instructions from the downstream skills. Instead, identify the task type quickly, prefer the Obsidian CLI when practical, then load the matching specialized skill and follow it.

## CLI First

Prefer `obsidian` CLI commands when they can answer or perform the task with less context:

- list/search/read vault content
- create notes, especially from templates
- append/prepend content
- manage properties, aliases, tags, backlinks, tasks, daily notes, and bases
- run app commands, plugin/theme reloads, screenshots, DOM inspection, and console/error checks

Before assuming the CLI is unavailable, verify whether `obsidian` is actually on `PATH` in the current agent shell. In Codex or other sandboxed app environments, the user's interactive shell `PATH` may differ from the agent's `PATH`. If `obsidian` is not found, try likely absolute binary paths before falling back, especially on macOS:

- `/Applications/Obsidian.app/Contents/MacOS/obsidian`

If an absolute path works, continue using it for the rest of the task instead of concluding that the CLI is missing.

Use direct filesystem reads/edits when the CLI cannot do the operation precisely, when patching an existing file is cleaner, or when verification requires comparing exact file content.

## Required Discovery Before Creating Notes

Before creating any new Obsidian note, first inspect the vault for the user's existing structure.

1. Verify which vault/workspace path is actually in use, using the skill or explicit user instruction as the primary source of truth.
2. Search for existing notes of the same type and their folder location.
3. Search for templates and `.obsidian` configuration before inventing note structure.
4. Reuse the discovered template, folder, and property names as the source of truth.

If no matching template, folder convention, or example note exists, do not invent a schema silently. Ask the user only for the missing required fields or explain that the vault appears not to contain the expected template/configuration.

If a template exists, inspect which user-provided fields it expects. When the user asks to create the note, do not silently leave meaningful fields blank if they are not derivable from the provided materials. Ask for the missing values in one concise batch before finalizing the note, unless the user explicitly asked for a draft with placeholders.

## Routing

Choose the best match:

- `obsidian-markdown`: editing or creating Obsidian notes, wikilinks, embeds, callouts, frontmatter, tags, note cleanup, note structure, templates, or general `.md` work inside a vault
- `obsidian-bases`: creating or editing `.base` files, views, filters, formulas, dashboards, and database-like note views
- `json-canvas`: creating or editing `.canvas` files, mind maps, diagrams, concept maps, node layouts, and canvas connections
- `obsidian-cli`: interacting with a running Obsidian app via the `obsidian` CLI, vault search, note operations, tasks, properties, plugin development, theme development, screenshots, DOM inspection, and debugging
- `obsidian-template-create`: creating notes or vault records from existing Obsidian templates
- `obsidian-template-update`: updating concise per-template creation instructions after user feedback
- `defuddle`: extracting a normal web page into clean markdown before saving or importing it into the vault

## Selection Rules

1. If the user explicitly names one of the specialized skills, use it.
2. If the task can be done cleanly through `obsidian`, use `obsidian-cli` or a template skill that uses the CLI.
3. If the user asks to create a note/item from a template, use `obsidian-template-create` after first confirming the template exists in the current vault.
4. If the user says what was wrong with a previous template-created note, use `obsidian-template-update`.
5. If the request mentions a file extension, route by file type:
   - `.md` -> `obsidian-markdown`
   - `.base` -> `obsidian-bases`
   - `.canvas` -> `json-canvas`
6. If the request is about searching, automation, plugin or theme work, or controlling a running Obsidian app, use `obsidian-cli`.
7. If the request starts from a URL or article and the goal is to bring it into the vault as readable markdown, use `defuddle` first, then `obsidian-template-create` or `obsidian-markdown` if further note formatting is needed.
8. If the request mixes formats, use the smallest set of skills needed, in sequence.

## Common Sequences

- Web article -> `defuddle` -> `obsidian-markdown`
- New note or record -> inspect vault structure/templates first -> identify all missing user-provided fields -> ask for them in one concise batch if needed -> `obsidian-template-create` if a real template exists, otherwise `obsidian-markdown` plus a brief clarification for missing schema
- Template correction feedback -> `obsidian-template-update`
- Notes dashboard -> `obsidian-bases` and optionally `obsidian-markdown`
- Brainstorm to visual map -> `json-canvas`
- Plugin or theme change -> `obsidian-cli`

## Fallback

If the request is clearly Obsidian-related but ambiguous, start with `obsidian-cli` to inspect or act cheaply. Fall back to `obsidian-markdown` only when content-level markdown editing is the main task.

Never assume note location, frontmatter keys, or template fields from the task description alone when the user's vault can be inspected directly.
Never treat obviously meaningful empty fields such as store, price, buy-again flags, ratings, or notes as acceptable final output unless the user explicitly wants a partial draft.
