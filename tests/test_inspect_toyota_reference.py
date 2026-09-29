from pathlib import Path

from scripts.inspect_toyota_reference import main


def test_script_module_is_importable() -> None:
    assert Path(main.__code__.co_filename).name == "inspect_toyota_reference.py"
