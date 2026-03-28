"""PhantomAPI — Tool-call parser.

Extracts structured tool-call JSON from ChatGPT's free-form text
responses, converting them into OpenAI-compatible function call objects.
"""

import json
import re
import uuid


def parse_tool_calls(response_text: str) -> list[dict] | None:
    """Attempt to extract tool_calls JSON from the response text.

    Returns a list of OpenAI-compatible tool-call dicts, or None if
    no valid tool calls were found.
    """
    cleaned = response_text.strip()

    # Strip markdown code fences if present
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()

    # Build candidate strings to try parsing
    candidates = [cleaned]
    json_match = re.search(r'\{[\s\S]*"tool_calls"[\s\S]*\}', cleaned)
    if json_match:
        candidates.append(json_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "tool_calls" in parsed:
                raw_calls = parsed["tool_calls"]
                if isinstance(raw_calls, list) and len(raw_calls) > 0:
                    return _format_calls(raw_calls)
        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    return None


def _format_calls(raw_calls: list[dict]) -> list[dict]:
    """Convert raw parsed tool calls into the OpenAI function-call schema."""
    formatted = []
    for call in raw_calls:
        tool_name = call.get("name", "")
        arguments = call.get("arguments", {})
        arguments_str = (
            json.dumps(arguments, ensure_ascii=False)
            if isinstance(arguments, dict)
            else str(arguments)
        )
        formatted.append(
            {
                "id": f"call_{uuid.uuid4().hex[:24]}",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": arguments_str,
                },
            }
        )
    return formatted
