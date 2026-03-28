"""PhantomAPI — Smart prompt builder.

Converts OpenAI-style messages (with optional tool definitions)
into a single flat prompt string suitable for the ChatGPT web UI.
"""

from typing import Any


def format_prompt(messages: list[dict[str, Any]], tools: list | None = None) -> str:
    """Build a single prompt string from a list of OpenAI-format messages.

    When *tools* are provided and no tool results are present in the
    conversation, inject strict JSON-output instructions so ChatGPT
    returns parseable tool-call JSON instead of natural language.
    """
    parts: list[str] = []
    system_parts: list[str] = []
    has_tool_results = False
    user_question = ""

    for msg in messages:
        role = msg.get("role", "")
        msg_type = msg.get("type", "")
        content = msg.get("content", "")

        # Normalise list-style content (multimodal messages)
        if isinstance(content, list):
            text_bits = []
            for item in content:
                if isinstance(item, dict):
                    text_bits.append(item.get("text", item.get("content", str(item))))
                else:
                    text_bits.append(str(item))
            content = "\n".join(text_bits)

        if role == "system":
            system_parts.append(content)

        elif role == "tool":
            has_tool_results = True
            tool_name = msg.get("name", "tool")
            parts.append(f"[TOOL RESULT from '{tool_name}']:\n{content}")

        elif msg_type == "function_call_output":
            has_tool_results = True
            call_id = msg.get("call_id", "")
            output = msg.get("output", content)
            parts.append(f"[TOOL RESULT (call_id: {call_id})]:\n{output}")

        elif msg_type == "function_call":
            func_name = msg.get("name", "?")
            func_args = msg.get("arguments", "{}")
            parts.append(f"[PREVIOUS TOOL CALL: Called '{func_name}' with arguments: {func_args}]")

        elif role == "assistant":
            assistant_text = content or ""
            tool_calls_in_msg = msg.get("tool_calls", [])
            if tool_calls_in_msg:
                tc_descs = []
                for tc in tool_calls_in_msg:
                    func = tc.get("function", {})
                    tc_descs.append(f"Called '{func.get('name', '?')}' with: {func.get('arguments', '{}')}")
                assistant_text += "\n[Previous tool calls: " + "; ".join(tc_descs) + "]"
            if assistant_text.strip():
                parts.append(f"[Assistant]: {assistant_text}")

        elif role == "user" or (msg_type == "message" and role != "system"):
            user_question = content
            parts.append(content)
            has_tool_results = False

        elif content:
            parts.append(content)

    # --- Build final prompt ---
    final = ""

    if system_parts:
        if tools and not has_tool_results:
            final += "=== YOUR ROLE ===\n"
            final += "\n\n".join(system_parts)
            final += "\n=== END OF ROLE ===\n\n"
        else:
            final += "=== SYSTEM INSTRUCTIONS (FOLLOW STRICTLY) ===\n"
            final += "\n\n".join(system_parts)
            final += "\n=== END OF INSTRUCTIONS ===\n\n"

    if tools and not has_tool_results:
        final += _format_tools_instruction(tools, user_question)

    if has_tool_results:
        final += "=== CONTEXT FROM TOOLS ===\n"
        final += "The following information was retrieved by the tools you requested.\n"
        final += "Use ONLY this information to answer the user's question.\n\n"

    if parts:
        final += "\n".join(parts)

    if has_tool_results:
        final += "\n\n=== INSTRUCTION ===\n"
        final += "Now answer the user's question based ONLY on the tool results above.\n"

    return final


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _format_tools_instruction(tools: list[dict], user_question: str = "") -> str:
    """Generate the mandatory tool-usage block injected into the prompt."""
    instruction = "\n=== MANDATORY TOOL USAGE ===\n"
    instruction += "You MUST use one of the tools below to answer this question.\n"
    instruction += "Do NOT answer directly. Do NOT say you don't have information.\n"
    instruction += "You MUST respond with ONLY a JSON object to call the tool.\n\n"

    instruction += "RESPONSE FORMAT - respond with ONLY this JSON, nothing else:\n"
    instruction += '{"tool_calls": [{"name": "TOOL_NAME", "arguments": {"param": "value"}}]}\n\n'

    instruction += "RULES:\n"
    instruction += "- Your ENTIRE response must be valid JSON only\n"
    instruction += "- No markdown, no code blocks, no explanation\n"
    instruction += "- No text before or after the JSON\n\n"

    instruction += "Available tools:\n\n"

    for tool in tools:
        func = tool.get("function", tool)
        name = func.get("name", "unknown")
        desc = func.get("description", "No description")
        params = func.get("parameters", {})

        instruction += f"Tool: {name}\n"
        instruction += f"Description: {desc}\n"

        if params.get("properties"):
            instruction += "Parameters:\n"
            required_params = params.get("required", [])
            for pname, pinfo in params["properties"].items():
                ptype = pinfo.get("type", "string")
                pdesc = pinfo.get("description", "")
                req = "required" if pname in required_params else "optional"
                instruction += f"  - {pname} ({ptype}, {req}): {pdesc}\n"
        instruction += "\n"

    instruction += "=== END OF TOOLS ===\n\n"

    first_tool = tools[0] if tools else {}
    first_func = first_tool.get("function", first_tool)
    first_name = first_func.get("name", "tool")

    instruction += "EXAMPLE: If the user asks a question, respond with:\n"
    instruction += '{"tool_calls": [{"name": "' + first_name + '", "arguments": {"input": "the user question here"}}]}\n\n'
    instruction += "Now respond with the JSON to call the appropriate tool:\n\n"

    return instruction
