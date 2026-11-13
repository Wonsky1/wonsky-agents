"""Pure ledger header, template and proposal transformations."""
import datetime as dt
from pathlib import Path
import re
from typing import List, Optional

from session_ledger.identity import binding
from session_ledger.models.ledger import Binding, Ledger, LedgerError

HEADER_RE = re.compile(r'^ledger: (?P<path>.+?) \| id: (?P<id>\S+) \| sessions: (?P<sessions>[^|]*?) \| created: (?P<created>\S+)\s*$', re.M)


def parse_header(path: Path, text: str) -> Ledger:
    lines = text.splitlines()
    match = HEADER_RE.fullmatch(lines[1]) if len(lines) > 1 else None
    if not match:
        raise LedgerError('no valid second-line ledger header in ' + str(path))
    sessions = []
    for item in match['sessions'].split(','):
        item = item.strip()
        if not item or item == '-':
            continue
        host, separator, session = item.partition(':')
        sessions.append(binding(host, session) if separator else binding('generic', item))
    return Ledger(path, match['id'], tuple(sessions), match['created'])


def add_binding(text: str, identity: Binding) -> str:
    match = HEADER_RE.search(text)
    if match is None:
        raise LedgerError('missing ledger header')
    current = match['sessions'].strip()
    updated = identity.key if current in ('', '-') else current + ', ' + identity.key
    start, end = match.span('sessions')
    return text[:start] + updated + text[end:]


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40].strip('-') or 'task'


def render(template: str, slug: str, relative: str, identifier: str,
           identity: Optional[Binding], today: dt.date) -> str:
    values = {'slug': slugify(slug), 'path': relative, 'id': identifier,
              'sessions': identity.key if identity else '-', 'created': today.isoformat()}
    return re.sub(r'\{(slug|path|id|sessions|created)\}', lambda match: values[match[1]], template)


def pending_proposals(text: str) -> List[str]:
    section = re.search(r'^## D\..*?(?=^## |\Z)', text, re.M | re.S)
    if not section:
        return []
    pending = []
    for line in section[0].splitlines():
        tag = re.search(r'\[durable(?::\s*(?P<state>\w+))?[^\]]*\]', line, re.I)
        if tag and (tag['state'] or 'pending').lower() in ('pending', 'proposed'):
            pending.append(line.strip())
    return pending
