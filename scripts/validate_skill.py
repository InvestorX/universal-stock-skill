from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc

    metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(metadata, dict):
        raise TypeError("SKILL.md frontmatter must be a YAML mapping")

    return metadata, "\n".join(lines[end + 1 :])


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    path = skill_dir / "SKILL.md"

    if not path.is_file():
        return [f"missing required file: {path}"]

    try:
        metadata, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        return [str(exc)]

    name = metadata.get("name")
    description = metadata.get("description")

    if not isinstance(name, str) or not name:
        errors.append("frontmatter.name is required")
    else:
        if len(name) > 64:
            errors.append("frontmatter.name must be <= 64 characters")
        if not NAME_RE.fullmatch(name):
            errors.append(
                "frontmatter.name must use lowercase letters, digits, and hyphens"
            )
        if name != skill_dir.name:
            errors.append("frontmatter.name must match the skill directory name")

    if not isinstance(description, str) or not description.strip():
        errors.append("frontmatter.description is required")
    elif len(description) > 1024:
        errors.append("frontmatter.description must be <= 1024 characters")

    if not body.strip():
        errors.append("SKILL.md body must not be empty")

    if len(body.splitlines()) > 500:
        errors.append("SKILL.md body should remain <= 500 lines")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "skill_dir",
        nargs="?",
        type=Path,
        default=Path(".agents/skills/stock-analysis"),
    )
    args = parser.parse_args()

    errors = validate_skill(args.skill_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {args.skill_dir / 'SKILL.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
