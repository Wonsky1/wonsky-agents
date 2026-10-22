#!/usr/bin/env python3
"""Read-only scope discovery, local Markdown links, and explicit-file digests.

Discovery never reads instructions and examines only the repository ancestor
chain plus explicitly named global files. Host-specific candidates do not imply
precedence. The link checker does not crawl targets or check anchors, and is a
small Markdown subset: inline/reference links (including images), fenced and
indented code, and inline code. HTML links, MDX, nested link labels and complex
container/fence syntax need manual review. No helper grants filesystem access.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


def inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def existing(value):
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file() and not path.is_dir():
        raise ValueError("Expected a regular file or directory: {}".format(path))
    return path


def git_root(requested):
    # Ask Git from before the first symlink, so a link into another repository
    # cannot silently substitute that repository for the user's lexical target.
    lexical = Path(os.path.abspath(os.path.expanduser(str(requested))))
    anchor = lexical if lexical.is_dir() else lexical.parent
    for component in reversed([lexical] + list(lexical.parents)):
        if component.is_symlink():
            anchor = component.parent
            break
    result = subprocess.run(
        ["git", "-C", str(anchor), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=10,
    )
    if result.returncode:
        raise ValueError("No Git repository found; provide --repo-root for a non-Git tree")
    return existing(result.stdout.strip())


def candidate(path, root=None, kind="instruction"):
    resolved = path.resolve()
    result = {"path": str(path), "resolved_path": str(resolved), "kind": kind}
    if root is not None and not inside(resolved, root):
        result["status"] = "outside_repository"
    elif not resolved.exists():
        result["status"] = "missing"
    elif not resolved.is_file():
        result["status"] = "not_a_file"
    else:
        result["status"] = "discovered"
    return result


def discover(path, repo_root=None, global_instructions=()):
    scope = existing(path)
    root = existing(repo_root) if repo_root else git_root(path)
    if not root.is_dir():
        raise ValueError("Repository root must be a directory")
    if not inside(scope, root):
        raise ValueError("Resolved task path escapes repository root: {}".format(scope))
    scope_dir = scope if scope.is_dir() else scope.parent
    chain = []
    current = scope_dir
    while True:
        chain.append(current)
        if current == root:
            break
        current = current.parent
    instructions = []
    for directory in reversed(chain):
        for name in ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md"):
            item = directory / name
            if item.exists() or item.is_symlink():
                instructions.append(candidate(
                    item, root, "ancestor_instruction" if name == "AGENTS.md"
                    else "host_specific_candidate",
                ))
    globals_ = [candidate(Path(p).expanduser().absolute(), kind="explicit_global_instruction")
                for p in global_instructions]
    return {
        "repository_root": str(root), "scope_path": str(scope),
        "scope_kind": "directory" if scope.is_dir() else "file",
        "ancestor_directories": [str(p) for p in reversed(chain)],
        "instruction_candidates": instructions,
        "global_instruction_candidates": globals_,
        "context_index": candidate(root / "docs/agent-context/index.md", root, "context_index"),
        "contents_read": False,
        "notice": "Candidates only; host precedence and actual document reads must be established by the agent.",
    }


def prose_only(text):
    """Mask code/comments with spaces, retaining positions for line numbers."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if re.match(r"^ {0,3}" + re.escape(fence[0]) + r"{" + str(fence[1]) + r",}\s*$", line):
                fence = None
            lines.append(re.sub(r"[^\n]", " ", line))
        elif marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            lines.append(re.sub(r"[^\n]", " ", line))
        elif line.startswith("    ") or line.startswith("\t"):
            lines.append(re.sub(r"[^\n]", " ", line))
        else:
            lines.append(line)
    text = "".join(lines)
    mask = lambda match: re.sub(r"[^\n]", " ", match.group(0))
    text = re.sub(r"<!--[\s\S]*?-->", mask, text)
    return re.sub(r"(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)", mask, text)


def destination(value):
    value = value.strip()
    if value.startswith("<"):
        end = value.find(">")
        return value[1:end] if end >= 0 else value
    # A trailing quoted title is not part of the path. Unquoted spaces are
    # accepted as a convenience; angle brackets are recommended for portability.
    value = re.sub(r'\s+(?:"[^"\n]*"|\x27[^\x27\n]*\x27|\([^()\n]*\))\s*$', "", value)
    return re.sub(r"\\([\\()\[\] <>])", r"\1", value)


def label_key(label):
    return " ".join(label.split()).casefold()


def markdown_links(text):
    text = prose_only(text)
    definitions = {}
    definition_pattern = re.compile(r"^ {0,3}\[([^\]\n]+)\]:[ \t]*(.+)$", re.MULTILINE)
    for match in definition_pattern.finditer(text):
        definitions.setdefault(label_key(match.group(1)), destination(match.group(2)))
    text = definition_pattern.sub(lambda m: " " * len(m.group(0)), text)
    pattern = re.compile(r"(?<!!)(?:!)?\[([^\]\n]+)\]")
    consumed = 0
    for match in pattern.finditer(text):
        if match.start() < consumed:
            continue
        pos = match.end()
        target = None
        if pos < len(text) and text[pos] == "(":
            start = pos + 1
            depth, angle, escaped = 1, False, False
            pos += 1
            while pos < len(text):
                char = text[pos]
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "<":
                    angle = True
                elif char == ">":
                    angle = False
                elif not angle and char == "(":
                    depth += 1
                elif not angle and char == ")":
                    depth -= 1
                    if depth == 0:
                        target = destination(text[start:pos])
                        consumed = pos + 1
                        break
                pos += 1
        elif pos < len(text) and text[pos] == "[":
            end = text.find("]", pos + 1)
            if end >= 0:
                label = text[pos + 1:end] or match.group(1)
                target = definitions.get(label_key(label))
                consumed = end + 1
                if target is None:
                    yield None, text.count("\n", 0, match.start()) + 1, label
        else:
            target = definitions.get(label_key(match.group(1)))
        if target is not None:
            yield target, text.count("\n", 0, match.start()) + 1, None


def check_links(file, repo_root):
    root = existing(repo_root)
    if not root.is_dir():
        raise ValueError("Repository root must be a directory")
    source = existing(file)
    if not inside(source, root) or not source.is_file():
        raise ValueError("Markdown source must be a file inside the repository")
    links, ignored = [], 0
    for target, line, missing_ref in markdown_links(source.read_text(encoding="utf-8")):
        if missing_ref is not None:
            links.append({"line": line, "reference": missing_ref, "status": "undefined_reference"})
            continue
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            ignored += 1
            continue
        local_path = Path(unquote(parsed.path))
        resolved = (source.parent / local_path).resolve()
        status = "outside_repository" if not inside(resolved, root) else (
            "exists" if resolved.exists() else "missing")
        links.append({"line": line, "target": target, "resolved_path": str(resolved), "status": status})
    return {
        "source": str(source), "repository_root": str(root), "links": links,
        "ignored_external_or_anchor_links": ignored,
        "ok": all(link["status"] == "exists" for link in links),
        "limitations": "Explicit file only; no target traversal, anchor validation, HTML/MDX or full CommonMark parsing.",
    }


def fingerprint(files):
    results = []
    for file in files:
        path = existing(file)
        if not path.is_file():
            raise ValueError("Fingerprint requires a file: {}".format(path))
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(65536), b""):
                digest.update(block)
                size += len(block)
        results.append({"path": str(path), "sha256": digest.hexdigest(), "size_bytes": size})
    return {"files": results, "notice": "Digests establish file identity, not that an agent has read or applied the contents."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    discovery = commands.add_parser("discover")
    discovery.add_argument("path")
    discovery.add_argument("--repo-root")
    discovery.add_argument("--global-instruction", action="append", default=[])
    links = commands.add_parser("check-links")
    links.add_argument("file")
    links.add_argument("--repo-root", required=True)
    fingerprints = commands.add_parser("fingerprint")
    fingerprints.add_argument("files", nargs="+")
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            result = discover(args.path, args.repo_root, args.global_instruction)
        elif args.command == "check-links":
            result = check_links(args.file, args.repo_root)
        else:
            result = fingerprint(args.files)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("ok") is False else 0


if __name__ == "__main__":
    sys.exit(main())
