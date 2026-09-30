from __future__ import annotations

import argparse
import shutil
from pathlib import Path

AGENTS = ("codex", "claude", "antigravity", "hermes")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_skill() -> Path:
    return repo_root() / ".agents" / "skills" / "stock-analysis"


def destination(agent: str, scope: str, project_root: Path) -> Path:
    home = Path.home()

    if scope == "project":
        if agent == "claude":
            return project_root / ".claude" / "skills" / "stock-analysis"
        return project_root / ".agents" / "skills" / "stock-analysis"

    if agent == "codex":
        return home / ".agents" / "skills" / "stock-analysis"
    if agent == "claude":
        return home / ".claude" / "skills" / "stock-analysis"
    if agent == "antigravity":
        return home / ".gemini" / "antigravity-cli" / "skills" / "stock-analysis"
    if agent == "hermes":
        return home / ".hermes" / "skills" / "stock-analysis"

    raise ValueError(f"unsupported agent: {agent}")


def remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def install_one(
    agent: str,
    scope: str,
    project_root: Path,
    *,
    force: bool,
) -> Path:
    source = source_skill().resolve()
    dest = destination(agent, scope, project_root)

    try:
        if dest.exists() and dest.resolve() == source:
            print(f"{agent}: already active at {dest}")
            return dest
    except OSError:
        pass

    if dest.exists() or dest.is_symlink():
        if not force:
            raise FileExistsError(
                f"{dest} already exists; rerun with --force to replace it"
            )
        remove_existing(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)
    print(f"{agent}: installed {dest}")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install the portable stock-analysis Agent Skill."
    )
    parser.add_argument("--agent", choices=(*AGENTS, "all"), default="all")
    parser.add_argument("--scope", choices=("project", "user"), default="user")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    agents = AGENTS if args.agent == "all" else (args.agent,)
    seen: set[Path] = set()

    for agent in agents:
        dest = destination(agent, args.scope, args.project_root.resolve())
        if dest in seen:
            print(f"{agent}: shared project path already handled at {dest}")
            continue
        install_one(
            agent,
            args.scope,
            args.project_root.resolve(),
            force=args.force,
        )
        seen.add(dest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
