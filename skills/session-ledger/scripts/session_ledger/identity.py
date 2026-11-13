"""Host-qualified session identity; no assumed shell environment propagation."""
import re
from typing import Mapping, Optional

from session_ledger.models.ledger import Binding, LedgerError

HOSTS = ('generic', 'claude', 'codex', 'cursor', 'antigravity')
SAFE_SESSION = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')
HOST_ENV = {'claude': 'CLAUDE_CODE_SESSION_ID', 'codex': 'CODEX_THREAD_ID'}


def binding(host: str, session: str) -> Binding:
    if host not in HOSTS:
        raise LedgerError('unsupported host: ' + str(host))
    if not isinstance(session, str) or not SAFE_SESSION.fullmatch(session) or session == '-':
        raise LedgerError('unsupported session id: ' + repr(session))
    return Binding(host, session)


def select_binding(host: Optional[str], session: Optional[str], env: Mapping[str, str]) -> Optional[Binding]:
    """Explicit IDs win; host-specific environment IDs never cross host namespaces."""
    selected_host = host or env.get('AGENT_HOST') or 'generic'
    if selected_host not in HOSTS:
        raise LedgerError('unsupported host: ' + selected_host)
    if session is not None:
        return binding(selected_host, session)
    if env.get('AGENT_SESSION_ID'):
        return binding(selected_host, env['AGENT_SESSION_ID'])
    if selected_host in HOST_ENV and env.get(HOST_ENV[selected_host]):
        return binding(selected_host, env[HOST_ENV[selected_host]])
    if host is None and not env.get('AGENT_HOST'):
        candidates = [binding(name, env[var]) for name, var in HOST_ENV.items() if env.get(var)]
        if len(candidates) > 1:
            raise LedgerError('multiple host session IDs; pass --host and --session explicitly')
        if candidates:
            return candidates[0]
    return None
