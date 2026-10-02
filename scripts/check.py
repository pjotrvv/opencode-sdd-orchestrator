#!/usr/bin/env python3
"""Structural check for this pack, plus drift check against spec-kit's templates.

Every assertion runs offline except the spec-kit fetch: when GitHub is
unreachable (rate limit, no network) that half prints SKIP and the structural
checks still decide the exit code.

Usage:
    python3 scripts/check.py [path-to-spec-kit-checkout]
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CMD = ROOT / ".opencode" / "commands" / "sdd.md"
SKILL = ROOT / ".opencode" / "skills" / "sdd-orchestrator" / "SKILL.md"
LICENSE = ROOT / "LICENSE"
TEMPLATE_URL = "https://api.github.com/repos/github/spec-kit/contents/templates/commands"
CORE_STAGES = {"constitution", "specify", "plan", "tasks", "implement", "converge"}

failures = []


def report(ok, label):
    print(("ok   " if ok else "FAIL ") + label)
    if not ok:
        failures.append(label)


def frontmatter(text):
    """Return (fields, ok). Simple key: value parsing with line continuation."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, False
    fields, key = {}, None
    for line in m.group(1).splitlines():
        if line[:1] in (" ", "\t") and key:
            fields[key] += " " + line.strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip()
    return fields, True


def spec_kit_templates(spec_dir=None):
    """Available template stems, or None when unreachable (caller prints SKIP)."""
    if spec_dir:
        return {p.stem for p in (spec_dir / "templates" / "commands").glob("*.md")}
    try:
        with urllib.request.urlopen(TEMPLATE_URL, timeout=30) as resp:
            data = json.load(resp)
        return {entry["name"][: -len(".md")] for entry in data if entry["name"].endswith(".md")}
    except Exception as exc:  # network, rate limit, API shape change
        print(f"SKIP  spec-kit templates unreachable ({exc.__class__.__name__}: {exc})")
        return None


def main(argv):
    cmd_text = CMD.read_text()
    cmd_fields, cmd_ok = frontmatter(cmd_text)
    report(cmd_ok, "sdd.md has parseable frontmatter")
    report(bool(cmd_fields.get("description")), "sdd.md declares a description")
    report("$ARGUMENTS" in cmd_text, "sdd.md expands $ARGUMENTS")

    skill_text = SKILL.read_text()
    skill_fields, skill_ok = frontmatter(skill_text)
    report(skill_ok, "SKILL.md has parseable frontmatter")
    report(bool(skill_fields.get("name")), "SKILL.md declares a name")
    report(bool(skill_fields.get("description")), "SKILL.md declares a description")

    referenced = set(re.findall(r"/speckit\.([a-z]+)", skill_text))
    report(
        CORE_STAGES <= referenced,
        f"all core stages referenced (missing: {sorted(CORE_STAGES - referenced)})",
    )
    report(LICENSE.read_text().startswith("MIT License"), "LICENSE is MIT")

    available = spec_kit_templates(Path(argv[1]) if len(argv) > 1 else None)
    if available is not None:
        stale = referenced - available
        report(
            not stale,
            f"every /speckit.* name ships upstream (stale: {sorted(stale)})",
        )

    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
