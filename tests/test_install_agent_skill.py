from pathlib import Path

from scripts.install_agent_skill import destination


def test_project_paths_delegate_to_shared_agents_directory() -> None:
    root = Path("/tmp/project")

    assert destination("codex", "project", root) == (
        root / ".agents" / "skills" / "stock-analysis"
    )
    assert destination("antigravity", "project", root) == (
        root / ".agents" / "skills" / "stock-analysis"
    )
    assert destination("hermes", "project", root) == (
        root / ".agents" / "skills" / "stock-analysis"
    )
    assert destination("claude", "project", root) == (
        root / ".claude" / "skills" / "stock-analysis"
    )
