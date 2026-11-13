"""Host capability boundary for the explicitly invoked remote-server skill."""

from typing import Optional


def distribution_issue(skill_name: str, target_key: str,
                       destination_exists: bool = False) -> Optional[str]:
    """Explain exclusions without inspecting files or altering installed copies."""
    if skill_name != 'remote-server' or target_key in ('codex', 'claude', 'cursor'):
        return None
    reason = 'remote-server is manual-only; this destination cannot guarantee explicit invocation'
    if destination_exists:
        return 'blocked: {}; existing copy preserved, remove it from automatic discovery manually'.format(reason)
    return 'skipped: {}'.format(reason)
