import pytest

from universal_stock_skill.llm import ToolDefinition
from universal_stock_skill.runtime.tools import ToolRegistry


@pytest.mark.asyncio
async def test_tool_registry_executes_registered_tool() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="double",
            description="Double a number",
            input_schema={
                "type": "object",
                "properties": {"value": {"type": "number"}},
                "required": ["value"],
            },
        ),
        lambda args: {"result": args["value"] * 2},
    )

    result = await registry.execute("double", {"value": 21})
    assert result == {"result": 42}


@pytest.mark.asyncio
async def test_unknown_tool_is_rejected() -> None:
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        await registry.execute("missing", {})
