"""Render exact update evidence and collect whole-unit choices."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping


def token(plan) -> str:
    data = {'destination': str(plan.destination), 'new': dict(plan.new_hashes),
            'previous': dict(plan.previous_hashes), 'local': plan.local_fingerprint,
            'state': hashlib.sha256(plan.state_fingerprint).hexdigest() if plan.state_fingerprint is not None else None,
            'blocked': plan.blocked}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def default_choice(plan) -> str:
    return 'keep' if plan.conflicts or plan.blocked else 'update'


def private_path(name: str) -> bool:
    return Path(name).name.casefold() == 'reviewer-preferences.md' or any(
        part.casefold().startswith('.env') and part.casefold() != '.env.example' for part in Path(name).parts)


def describe(plan) -> str:
    lines = ['{}\nDestination: {}\nStatus: {}'.format(plan.label, plan.destination, plan.status)]
    if plan.unknown_original:
        lines.append('Original version unknown. Local-to-new comparisons are not a reconstruction of manual edits.')
    for label, changes in (('LOCAL CHANGES', plan.local_changes),
                           ('OFFERED VERSION CHANGES', plan.upstream_changes),
                           ('REPLACEMENT WOULD CHANGE', plan.replacement_changes)):
        if changes:
            lines.append('\n' + label)
        for change in changes:
            lines.append('{}: {} ({})'.format(change.path, change.kind, change.comparison))
            if private_path(change.path):
                lines.append('Private local file retained; content is omitted from the review report.')
            else:
                lines.append(change.diff)
    if plan.preserved:
        lines.append('Preserved: ' + ', '.join(plan.preserved))
    if plan.blocked:
        lines.append('Blocked paths cannot be replaced: ' + ', '.join(plan.blocked))
    return '\n'.join(lines) + '\n'


def _change_data(change):
    data = asdict(change)
    if private_path(change.path):
        data['diff'] = 'Private local file retained; content omitted.'
    return data


def report_data(plans: list, choices: Mapping[str, str], revision: str) -> dict:
    return {'kind': 'wonsky-agents-update-review', 'version': 1, 'source_revision': revision,
            'choices': {plan.id: {'choice': choices[plan.id], 'token': token(plan)} for plan in plans},
            'plans': [{'id': plan.id, 'label': plan.label, 'status': plan.status,
                       'unknown_original': plan.unknown_original, 'blocked': list(plan.blocked),
                       'preserved': list(plan.preserved),
                       'local_changes': [_change_data(change) for change in plan.local_changes],
                       'upstream_changes': [_change_data(change) for change in plan.upstream_changes],
                       'replacement_changes': [_change_data(change) for change in plan.replacement_changes]}
                      for plan in plans]}


def load_decisions(path: Path, revision: str) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('version') != 1 or data.get('source_revision') != revision or not isinstance(data.get('choices'), dict):
        raise ValueError('Decisions do not match this source revision; create a new preview.')
    return data['choices']


def reviewed_choices(plans: list, decisions: dict, require_all: bool = False) -> dict:
    result = {}
    for plan in plans:
        saved = decisions.get(plan.id)
        if saved is None:
            if require_all:
                raise ValueError('Missing reviewed choice for {}; preview the full resulting plan first.'.format(plan.label))
            result[plan.id] = default_choice(plan)
            continue
        if not isinstance(saved, dict) or saved.get('token') != token(plan):
            raise ValueError('Files changed since review for {}; create a new preview.'.format(plan.label))
        choice = saved.get('choice')
        if choice not in ('keep', 'update', 'replace') or (plan.conflicts and choice == 'update') or (plan.blocked and choice != 'keep'):
            raise ValueError('Invalid or unsafe reviewed choice for {}'.format(plan.label))
        result[plan.id] = choice
    return result


def gui_choices(plans: list):
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        return None
    try:
        root = tk.Tk()
    except (tk.TclError, RuntimeError):
        return None
    root.title('Review Wonsky Agents update')
    root.geometry('1000x700')
    try:
        ttk.Label(root, text='Select a skill to inspect every changed file. Check Use new version only after reviewing its diff.').pack(padx=12, pady=8)
        body = ttk.Panedwindow(root, orient='horizontal')
        body.pack(fill='both', expand=True, padx=12)
        listing = tk.Listbox(body, width=38, exportselection=False)
        text_frame = ttk.Frame(body)
        text = tk.Text(text_frame, wrap='none')
        scroll = ttk.Scrollbar(text_frame, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        horizontal = ttk.Scrollbar(text_frame, orient='horizontal', command=text.xview)
        text.configure(xscrollcommand=horizontal.set)
        scroll.pack(side='right', fill='y')
        horizontal.pack(side='bottom', fill='x')
        text.pack(fill='both', expand=True)
        body.add(listing, weight=1)
        body.add(text_frame, weight=3)
        values = {plan.id: tk.BooleanVar(value=not plan.conflicts and not plan.blocked) for plan in plans}
        current = {'index': None}
        use_new = ttk.Checkbutton(root, text='Use new version (unchecked = keep this entire skill)')
        use_new.pack(anchor='w', padx=12, pady=8)
        for plan in plans:
            listing.insert('end', '{} | {}'.format(plan.status, plan.label))
        def select(event=None):
            selected = listing.curselection()
            if not selected:
                return
            index = selected[0]
            plan = plans[index]
            current['index'] = index
            text.configure(state='normal')
            text.delete('1.0', 'end')
            text.insert('1.0', describe(plan))
            text.configure(state='disabled')
            use_new.configure(variable=values[plan.id], state='disabled' if plan.blocked else 'normal')
        listing.bind('<<ListboxSelect>>', select)
        accepted = {'value': False}
        def accept():
            accepted['value'] = True
            root.quit()
        buttons = ttk.Frame(root)
        buttons.pack(fill='x', padx=12, pady=10)
        ttk.Button(buttons, text='Continue to final review', command=accept).pack(side='right')
        ttk.Button(buttons, text='Cancel', command=root.quit).pack(side='right', padx=8)
        root.protocol('WM_DELETE_WINDOW', root.quit)
        if plans:
            listing.selection_set(0)
            select()
        root.mainloop()
        if not accepted['value']:
            raise KeyboardInterrupt()
        return {plan.id: ('replace' if plan.conflicts else 'update') if values[plan.id].get() else 'keep' for plan in plans}
    finally:
        root.destroy()


def choose(plans: list, terminal: bool = False) -> dict:
    if not terminal:
        result = gui_choices(plans)
        if result is not None:
            return result
    if not sys.stdin.isatty():
        raise ValueError('Non-interactive updates need --dry-run, or a reviewed --decisions file with --yes.')
    result = {}
    for plan in plans:
        print(describe(plan))
        if plan.blocked:
            result[plan.id] = 'keep'
        elif plan.conflicts or plan.local_changes:
            answer = input('Keep this skill [k] or use the new version [n]? [k]: ').strip().lower()
            if answer not in ('', 'k', 'n'):
                raise ValueError('Choose k or n; no update was applied.')
            result[plan.id] = 'replace' if answer == 'n' else 'keep'
        else:
            result[plan.id] = 'update'
    return result


def confirm(terminal: bool = False) -> bool:
    if not terminal:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            try:
                return messagebox.askyesno('Apply reviewed update?', 'Apply the selected updates now? Replaced content will be backed up.', parent=root)
            finally:
                root.destroy()
        except ImportError:
            pass
        except (tk.TclError, RuntimeError):
            pass
    if not sys.stdin.isatty():
        raise ValueError('Final confirmation needs a terminal/GUI or explicit --yes with safe/reviewed choices.')
    return input('Apply this complete plan? [y/N]: ').strip().lower() == 'y'
