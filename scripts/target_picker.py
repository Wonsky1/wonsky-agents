"""Optional Tk checkboxes, with a dependency-free terminal fallback."""

import sys
from typing import List, Optional, Sequence

from scripts.agent_targets import Target


def gui_picker(targets: Sequence[Target]) -> Optional[List[str]]:
    # None means no graphical picker is available; [] means the user cancelled.
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        return None
    try:
        root = tk.Tk()
    except tk.TclError:
        return None
    try:
        root.title('Wonsky Agents')
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Select where to install skills').pack(anchor='w', pady=(0, 10))
        variables = []
        for target in targets:
            checked = tk.BooleanVar(value=target.detected)
            variables.append(checked)
            status = 'detected' if target.detected else 'not detected; create skills folder'
            ttk.Checkbutton(frame, text='{} ({})'.format(target.label, status), variable=checked).pack(anchor='w')
            ttk.Label(frame, text=str(target.path)).pack(anchor='w', padx=24, pady=(0, 8))
        result = []

        def confirm() -> None:
            result.extend(t.key for t, value in zip(targets, variables) if value.get())
            root.destroy()

        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=(10, 0))
        ttk.Button(buttons, text='Cancel', command=root.destroy).pack(side='right')
        ttk.Button(buttons, text='Install selected', command=confirm).pack(side='right', padx=8)
        root.protocol('WM_DELETE_WINDOW', root.destroy)
        root.mainloop()
        return result
    except tk.TclError:
        try:
            root.destroy()
        except tk.TclError:
            pass
        return None


def pick_targets(targets: Sequence[Target], terminal: bool = False) -> List[str]:
    if not sys.stdin.isatty():
        raise ValueError('Interactive selection needs a terminal. Use --targets or --all for unattended runs.')
    if not terminal:
        result = gui_picker(targets)
        if result is not None:
            return result
    selected = {t.key for t in targets if t.detected}
    while True:
        print('\nToggle numbers separated by spaces; Enter installs; a=all, n=none, q=cancel.')
        for index, target in enumerate(targets, start=1):
            print('  [{}] {}. {} ({})'.format('x' if target.key in selected else ' ', index,
                                             target.label, 'detected' if target.detected else 'not detected'))
        answer = input('> ').strip().lower()
        if not answer:
            return [t.key for t in targets if t.key in selected]
        if answer == 'q':
            return []
        if answer in ('a', 'n'):
            selected = {t.key for t in targets} if answer == 'a' else set()
            continue
        numbers = answer.split()
        if not all(n.isdecimal() and 1 <= int(n) <= len(targets) for n in numbers):
            print('Choose valid destination numbers.')
            continue
        for n in numbers:
            key = targets[int(n) - 1].key
            if key in selected:
                selected.remove(key)
            else:
                selected.add(key)
