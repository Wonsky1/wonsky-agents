"""Known agent destinations and installation evidence on each desktop OS."""

import os
from pathlib import Path
import shutil
from typing import Callable, List, Mapping, Optional, Sequence

from scripts.models.target import Target


def detect_targets(home: Path, system: str, environ: Mapping[str, str],
                   which: Callable[[str], Optional[str]] = shutil.which) -> List[Target]:
    codex = Path(environ.get('CODEX_HOME') or home / '.codex').expanduser()
    definitions = (
        ('cursor', 'Cursor', home / '.cursor', ('cursor',), 'Cursor'),
        ('claude', 'Claude Code', home / '.claude', ('claude',), 'Claude'),
        ('codex', 'Codex', codex, ('codex',), 'Codex'),
        ('antigravity', 'Antigravity', home / '.gemini/config', ('antigravity', 'agy'), 'Antigravity'),
        ('agents', 'Agents standard', home / '.agents', (), None),
    )
    targets = []
    for key, label, config, commands, app in definitions:
        evidence = [config]
        if app and system == 'Darwin':
            evidence.extend((Path('/Applications') / (app + '.app'),
                             home / 'Applications' / (app + '.app')))
        elif app and system == 'Windows':
            local = Path(environ.get('LOCALAPPDATA') or home / 'AppData/Local')
            roots = [local / 'Programs', local]
            for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
                if environ.get(variable):
                    roots.append(Path(environ[variable]))
            for root in roots:
                for folder in {app, app.lower()}:
                    evidence.append(root / folder / (app + '.exe'))
        elif app and system == 'Linux':
            data_home = Path(environ.get('XDG_DATA_HOME') or home / '.local/share')
            data_dirs = (environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(os.pathsep)
            roots = [data_home, *(Path(p) for p in data_dirs if p),
                     home / '.local/share/flatpak/exports/share',
                     Path('/var/lib/flatpak/exports/share')]
            evidence.extend(root / 'applications' / (key + '.desktop') for root in roots)
            xdg_config = Path(environ.get('XDG_CONFIG_HOME') or home / '.config')
            evidence.append(xdg_config / app)
        detected = any(p.exists() for p in evidence) or any(which(command) for command in commands)
        targets.append(Target(key, label, config / 'skills', detected))
    return targets


def select_keys(targets: Sequence[Target], requested: Optional[str], all_detected: bool) -> List[str]:
    if requested is not None:
        keys = list(dict.fromkeys(part.strip() for part in requested.split(',')))
        known = {t.key for t in targets}
        unknown = [key for key in keys if key not in known]
        if unknown:
            raise ValueError('Unknown target(s): {}. Available: {}'.format(', '.join(unknown), ', '.join(sorted(known))))
        return keys
    return [t.key for t in targets if t.detected] if all_detected else []
