"""Map stable canonical skill slugs to collection-owned runtime identifiers."""


def runtime_skill_name(canonical_name: str) -> str:
    """Keep source/helper paths stable while avoiding other collections' names."""
    return canonical_name if canonical_name.startswith('wa-') else 'wa-' + canonical_name
