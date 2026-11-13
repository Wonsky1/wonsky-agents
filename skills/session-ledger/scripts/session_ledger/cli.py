"""CLI argument parsing and presentation, delegating persistence to storage."""
import argparse
import os
from typing import List, Optional

from session_ledger.git import resolve_root
from session_ledger.hooks import HOOK_HOSTS, run_hook
from session_ledger.identity import HOSTS, select_binding
from session_ledger.markdown import pending_proposals
from session_ledger.models.ledger import LedgerError, Root
from session_ledger.storage import bind_session, find_ledger, load_ledger, new_ledger, read_ledgers, read_text


def identity_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--host', choices=HOSTS)
    parser.add_argument('--session')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Repository-local session ledgers; explicit identities across hosts.')
    sub = parser.add_subparsers(dest='command', required=True)
    new = sub.add_parser('new', help='create or return a ledger for a host/session')
    new.add_argument('--slug', required=True)
    new.add_argument('--repo')
    identity_arguments(new)
    for name in ('path', 'find'):
        finder = sub.add_parser(name, help='find a ledger by host/session or stable ledger ID')
        finder.add_argument('--repo')
        finder.add_argument('--host', choices=HOSTS)
        group = finder.add_mutually_exclusive_group()
        group.add_argument('--session')
        group.add_argument('--id', dest='identifier')
    lister = sub.add_parser('list')
    lister.add_argument('--repo')
    binder = sub.add_parser('bind')
    binder.add_argument('ledger')
    identity_arguments(binder)
    proposals = sub.add_parser('proposals')
    proposals.add_argument('ledger')
    hook = sub.add_parser('hook')
    hook.add_argument('--host', choices=HOOK_HOSTS, default='claude')
    hook.add_argument('--create', action='store_true')
    return parser


def warn_plain_root(root: Root) -> None:
    if not root.is_git:
        import sys
        print('ledger: not a Git repository; Git exclusion cannot be verified', file=sys.stderr)


def dispatch(args: argparse.Namespace) -> int:
    import sys
    if args.command == 'new':
        root = resolve_root(args.repo)
        identity = select_binding(args.host, args.session, os.environ)
        ledger = new_ledger(root, args.slug, identity)
        warn_plain_root(root)
        print(ledger.path.as_posix())
        if identity is None:
            print('ledger: no session identity; recover with path --id ' + ledger.identifier
                  + ' --repo ' + str(root.path), file=sys.stderr)
    elif args.command in ('path', 'find'):
        root = resolve_root(args.repo)
        identity = None if args.identifier else select_binding(args.host, args.session, os.environ)
        if identity is None and not args.identifier:
            raise LedgerError('no session id: pass --host and --session, or --id from the ledger header')
        ledger = find_ledger(root, identity, args.identifier)
        if ledger is None:
            print('ledger: no matching ledger; create with new --slug <task>', file=sys.stderr)
            return 1
        warn_plain_root(root)
        print(ledger.path.as_posix())
    elif args.command == 'list':
        root = resolve_root(args.repo)
        warn_plain_root(root)
        for ledger in read_ledgers(root):
            print(ledger.path.as_posix() + '\tid=' + ledger.identifier
                  + '\tsessions=' + (','.join(item.key for item in ledger.bindings) or '-'))
    elif args.command == 'bind':
        identity = select_binding(args.host, args.session, os.environ)
        if identity is None:
            raise LedgerError('no session id: pass --host and --session; use path --id for unbound recovery')
        changed = bind_session(args.ledger, identity)
        print(('bound ' if changed else 'already bound ') + identity.key)
    elif args.command == 'proposals':
        ledger = load_ledger(args.ledger)
        pending = pending_proposals(read_text(ledger.path))
        print('Context proposals: ' + str(len(pending)) + ' pending' if pending else 'Context proposals: none')
        for line in pending:
            print(line)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    import sys
    args = build_parser().parse_args(argv)
    if args.command == 'hook':
        return run_hook(args.host, args.create)
    try:
        return dispatch(args)
    except (LedgerError, OSError, ValueError, UnicodeError) as error:
        print('ledger: ' + str(error), file=sys.stderr)
        return 2
