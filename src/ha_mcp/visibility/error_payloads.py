"""Tool-error views for the visibility outbound scan.

A tool-raised error reaches the client as its JSON payload, so the scan needs the
same two checks a result gets: the flattened text the regexes match, and the
structured payloads for the trace ``domain`` + ``item_id`` records that name no
entity_id.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol

from .identifier_aliases import IdentifierAliases, is_trace_query, result_reveals_hidden

if TYPE_CHECKING:
    from ha_mcp._vendor.fastmcp.exceptions import ToolError


class HiddenIdMatcher(Protocol):
    """The hidden-set view the error scan needs.

    Structural so the enforcement module's matcher satisfies it without this
    module importing back into the enforcement module.
    """

    @property
    def identifier_aliases(self) -> IdentifierAliases: ...

    def embeds(self, text: str) -> bool: ...


def tool_error_text(exc: ToolError) -> str:
    """Flatten a tool error's args for scanning."""
    return "\n".join(str(arg) for arg in (getattr(exc, "args", None) or ()))


def tool_error_payloads(exc: ToolError) -> list[Any]:
    """A tool error's JSON args, parsed when they parse."""
    payloads: list[Any] = []
    for arg in getattr(exc, "args", None) or ():
        if not isinstance(arg, str):
            continue
        try:
            payloads.append(json.loads(arg))
        except json.JSONDecodeError:
            continue
    return payloads


def tool_error_reveals_hidden(
    exc: ToolError,
    tool_name: str,
    args: Mapping[str, Any],
    matcher: HiddenIdMatcher,
) -> bool:
    """Whether a tool error names a hidden id, trace ``item_id`` keys included."""
    return matcher.embeds(tool_error_text(exc)) or (
        is_trace_query(tool_name, args)
        and result_reveals_hidden(tool_error_payloads(exc), matcher.identifier_aliases)
    )
