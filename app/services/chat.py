"""PhantomAPI — Chat completion service.

All business logic for processing chat requests lives here.
Route handlers call these functions and return the result directly.
"""

import time
import uuid

from app.services.browser import engine
from app.utils.prompt import format_prompt
from app.utils.parser import parse_tool_calls


def process_chat_completion(messages: list, model: str, tools: list | None = None) -> dict:
    """Process a chat completion request and return an OpenAI-compatible response."""
    prompt = format_prompt(messages, tools=tools)
    start = time.time()

    print(f"[PhantomAPI] 📨 Request ({len(prompt)} chars)")
    response_text = engine.chat(prompt)

    p_tokens = len(prompt.split())
    c_tokens = len(response_text.split())
    tool_calls = parse_tool_calls(response_text) if tools else None

    return _build_chat_response(response_text, tool_calls, model, int(start), p_tokens, c_tokens)


def process_responses_api(messages: list, model: str, tools: list | None = None) -> dict:
    """Process a Responses API request and return the formatted response."""
    prompt = format_prompt(messages, tools=tools)
    start = time.time()

    response_text = engine.chat(prompt)

    p_tokens = len(prompt.split())
    c_tokens = len(response_text.split())
    tool_calls = parse_tool_calls(response_text) if tools else None

    return _build_responses_response(response_text, tool_calls, model, int(start), p_tokens, c_tokens)


# ---------------------------------------------------------------------------
# Private response builders
# ---------------------------------------------------------------------------

def _build_chat_response(
    text: str, tool_calls: list | None, model: str, created: int, p_tokens: int, c_tokens: int
) -> dict:
    """Build an OpenAI-compatible chat completion response dict."""
    response_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
    usage = {"prompt_tokens": p_tokens, "completion_tokens": c_tokens, "total_tokens": p_tokens + c_tokens}

    if tool_calls:
        message = {"role": "assistant", "content": None, "tool_calls": tool_calls}
        finish_reason = "tool_calls"
    else:
        message = {"role": "assistant", "content": text}
        finish_reason = "stop"

    return {
        "id": response_id,
        "object": "chat.completion",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        "usage": usage,
    }


def _build_responses_response(
    text: str, tool_calls: list | None, model: str, created: int, p_tokens: int, c_tokens: int
) -> dict:
    """Build a Responses API response dict."""
    response_id = f"resp-{uuid.uuid4().hex[:29]}"
    usage = {"input_tokens": p_tokens, "output_tokens": c_tokens, "total_tokens": p_tokens + c_tokens}

    if tool_calls:
        output = [
            {
                "type": "function_call",
                "id": tc["id"],
                "call_id": tc["id"],
                "name": tc["function"]["name"],
                "arguments": tc["function"]["arguments"],
                "status": "completed",
            }
            for tc in tool_calls
        ]
    else:
        output = [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            }
        ]

    return {
        "id": response_id,
        "object": "response",
        "created_at": created,
        "model": model,
        "status": "completed",
        "output": output,
        "usage": usage,
    }
