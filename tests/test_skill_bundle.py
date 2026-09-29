from pathlib import Path

import yaml

from scripts.validate_skill import split_frontmatter, validate_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "stock-analysis"


def test_portable_skill_manifest_is_valid() -> None:
    assert validate_skill(SKILL_DIR) == []


def test_skill_defaults_to_host_agent_without_endpoint() -> None:
    metadata, body = split_frontmatter(
        (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    )

    assert metadata["name"] == "stock-analysis"
    assert "host agent" in body.lower()
    assert (
        "do not ask the user to configure another llm endpoint"
        in body.lower()
    )

    internal = yaml.safe_load(
        (SKILL_DIR / "skill.yaml").read_text(encoding="utf-8")
    )
    assert internal["execution"]["default"] == "host-agent"
    assert internal["execution"]["endpoint_required"] is False
