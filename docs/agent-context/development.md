# Development

Python utilities use the standard library and support Python 3.9+. Read the [shared Python structure contract](../../skills/implementation-guide/references/python-structure.md) before design, implementation or review; it owns the detailed Python rules and required evidence.

From the repository root, run `python3 -B -m unittest discover -s tests -v` for the installer, `python3 -B -m unittest discover -s skills/repository-context/scripts/tests -v` for context utilities, and `python3 -B -m unittest discover -s skills/implementation-guide/scripts/tests -v` for structural checks. Tests use temporary repositories/homes. Run the read-only structure checker on the explicit changed Python paths and inspect semantic cohesion separately. A successful mechanical check cannot prove architectural quality.

Skill changes need scenario review of both the old failure and the revised behavior, not just keyword checks. Before completion, report the context outcome and verification evidence. Write useful factual drafts and ask the user to review them; keep any rule changes under exact approval. Sync approved canonical changes with `python3 -B install.py --sync-only --all`; inspect the target preview when destination selection is uncertain. Never copy personal reviewer preferences into version control.
