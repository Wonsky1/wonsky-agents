"""Host capability boundary for the explicitly invoked remote-server skill."""

from typing import Optional

from scripts.skills.names import runtime_skill_name


def distribution_names(skill_name: str, target_key: str) -> tuple:
    """Also inspect legacy manual-only copies on unsupported destinations."""
    installed = runtime_skill_name(skill_name)
    if distribution_issue(skill_name, target_key) and installed != skill_name:
        return installed, skill_name
    return (installed,)


def distribution_issue(skill_name: str, target_key: str,
                       destination_exists: bool = False) -> Optional[str]:
    """Explain exclusions without inspecting files or altering installed copies."""
    if skill_name != 'remote-server' or target_key in ('codex', 'claude', 'cursor', 'copilot'):
        return None
    reason = 'remote-server is manual-only; this destination cannot guarantee explicit invocation'
    if destination_exists:
        return 'blocked: {}; existing copy preserved, remove it from automatic discovery manually'.format(reason)
    return 'skipped: {}'.format(reason)
