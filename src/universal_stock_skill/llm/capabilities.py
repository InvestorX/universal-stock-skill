from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capabilities exposed by an LLM provider/model pair.

    The runtime uses these flags to decide whether to use native features or
    fall back to provider-neutral prompting/validation.
    """

    native_tool_calling: bool = False
    structured_output: bool = False
    json_schema: bool = False
    parallel_tool_calls: bool = False
