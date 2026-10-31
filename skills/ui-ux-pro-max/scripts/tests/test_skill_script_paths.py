"""Documented script commands resolve from this packaged skill, on any host."""

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
INVOCATION = re.compile(r'(?<![\w/.-])(?:python3?|node|bash)\s+"?([^\s"`\']+\.(?:py|cjs|js|mjs|sh))')


def resolve(path):
    if path.startswith("${SKILL_DIR}/"):
        return SKILL / path[len("${SKILL_DIR}/"):]
    if path.startswith("<skill-directory>/"):
        return SKILL / path[len("<skill-directory>/"):]
    if path.startswith("scripts/"):
        return SKILL / path
    if path.startswith("../"):
        parts = path.split("/")
        if len(parts) > 3 and parts[2] == "scripts":
            return SKILL.parent / parts[1] / "/".join(parts[2:])
    return None


class SkillScriptPathsTest(unittest.TestCase):
    def test_documented_commands_are_portable_and_ship_their_scripts(self):
        problems, seen = [], 0
        for md in sorted(SKILL.rglob("*.md")):
            for lineno, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
                for match in INVOCATION.finditer(line):
                    seen += 1
                    path = match.group(1)
                    target = resolve(path)
                    if target is None or not target.is_file():
                        problems.append(f"{md.relative_to(SKILL)}:{lineno}: {path}")
        self.assertGreater(seen, 0, "documented command extractor found no commands")
        self.assertEqual(problems, [], "Unresolved/nonportable commands: " + ", ".join(problems))


if __name__ == "__main__":
    unittest.main()
