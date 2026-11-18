"""Collection skills coexist with unrelated skills in every runtime root."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.installation.targets import detect_targets
from scripts.skills.names import runtime_skill_name
from scripts.updates.collection import canonical_plans, runtime_plans


ROOT = Path(__file__).resolve().parents[1]


class SkillNamespaceTests(unittest.TestCase):
    def test_already_namespaced_source_does_not_get_a_second_prefix(self):
        self.assertEqual(runtime_skill_name('wa-dev-pipeline'), 'wa-dev-pipeline')

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.package = self.root / 'package'
        shutil.copytree(ROOT / 'scripts', self.package / 'scripts',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copy2(ROOT / 'install.py', self.package / 'install.py')
        self.skill = self.package / 'skills/dev-pipeline'
        self.skill.mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text(
            '---\nname: wa-dev-pipeline\ndescription: Python workflow.\n---\n', encoding='utf-8')
        self.home = self.root / 'home'
        self.canonical = self.home / '.wonsky-agents'
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        CODEX_HOME=str(self.home / '.codex'), WONSKY_AGENTS_HOME=str(self.canonical))
        self.targets = detect_targets(self.home, 'Linux', self.env, lambda name: None)

    def install(self, *args):
        return subprocess.run([sys.executable, '-B', str(self.package / 'install.py'),
                               '--targets', ','.join(target.key for target in self.targets),
                               '--no-session-hooks', *args], env=self.env,
                              capture_output=True, text=True, timeout=30)

    def test_install_and_repeat_preserve_unrelated_unprefixed_skills(self):
        for target in self.targets:
            personal = target.path / 'dev-pipeline/SKILL.md'
            personal.parent.mkdir(parents=True)
            personal.write_text('personal workflow', encoding='utf-8')
        for arguments in ((), ('--sync-only',)):
            result = self.install(*arguments)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for target in self.targets:
                self.assertEqual((target.path / 'dev-pipeline/SKILL.md').read_text(), 'personal workflow')
                self.assertEqual((target.path / 'wa-dev-pipeline/SKILL.md').read_bytes(),
                                 (self.skill / 'SKILL.md').read_bytes())
                self.assertTrue((target.path / '.wonsky-state/wa-dev-pipeline.json').is_file())
        self.assertTrue((self.canonical / 'skills/dev-pipeline/SKILL.md').is_file())

    def test_preview_uses_namespaced_destinations_without_writes(self):
        result = self.install('--dry-run')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.home.exists())

    def test_installed_cross_skill_references_resolve_without_legacy_folders(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'install.py'),
                                 '--targets', 'codex', '--no-session-hooks'], env=self.env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        runtime = self.home / '.codex/skills'
        for slug in ('obsidian-cli', 'obsidian-bases', 'obsidian-markdown',
                     'json-canvas', 'macos-design-guidelines'):
            installed = runtime / ('wa-' + slug)
            references = re.findall(
                r'(?:~/.wonsky-agents/skills/|\.\./)(?:obsidian|swiftui-expert-skill)/SKILL.md',
                (installed / 'SKILL.md').read_text())
            self.assertTrue(references, slug)
            for reference in references:
                target = (self.home / reference[2:]) if reference.startswith('~/') else installed / reference
                self.assertTrue(target.is_file(), '{} -> {}'.format(slug, target))

    def test_updater_reviews_namespaced_destinations_and_leaves_personal_skills(self):
        plans = canonical_plans(self.package, self.canonical)
        choices = {plan.id: 'update' for plan in plans}
        for target in self.targets:
            personal = target.path / 'dev-pipeline/SKILL.md'
            personal.parent.mkdir(parents=True)
            personal.write_text('personal workflow', encoding='utf-8')
        runtimes = runtime_plans(plans, choices, self.targets)
        self.assertEqual({plan.destination for plan in runtimes},
                         {target.path / 'wa-dev-pipeline' for target in self.targets})
        self.assertTrue(all(plan.status == 'added' for plan in runtimes))
        self.assertTrue(all(plan.state_path.name == 'wa-dev-pipeline.json' for plan in runtimes))


if __name__ == '__main__':
    unittest.main()
