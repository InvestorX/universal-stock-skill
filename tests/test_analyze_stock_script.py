from pathlib import Path

from scripts.analyze_stock import main


def test_script_module_is_importable() -> None:
    assert Path(main.__code__.co_filename).name == "analyze_stock.py"
