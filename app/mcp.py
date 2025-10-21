from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .models import (
    Prompt,
    PromptRenderResponse,
    Resource,
    ToolArgument,
    ToolDefinition,
    ToolInvocationResponse,
)


RESOURCE_STORE: Dict[str, Resource] = {
    "company:outline": Resource(
        id="company:outline",
        title="Company Overview",
        description="High-level overview of the example company profile.",
        uri="mcp://resources/company-outline",
        mime_type="application/json",
        tags=["company", "knowledge-base"],
        data={
            "name": "Instrat Demo Co.",
            "mission": "Deliver AI-enabled productivity tooling.",
            "products": [
                "MCP integration services",
                "LLM consulting",
                "Automation toolkits",
            ],
        },
    ),
    "product:faq": Resource(
        id="product:faq",
        title="Product FAQ",
        description="Frequently asked questions for the flagship product.",
        uri="mcp://resources/product-faq",
        mime_type="application/json",
        tags=["faq", "support"],
        data={
            "deployment": "Docker or serverless",
            "uptime_sla": "99.9%",
            "support": "Email support within one business day",
        },
    ),
}


TOOL_DEFINITIONS: Dict[str, ToolDefinition] = {
    "math.add": ToolDefinition(
        name="math.add",
        description="Adds two numbers and returns the sum.",
        arguments=[
            ToolArgument(
                name="a",
                type="float",
                description="First addend.",
                required=True,
            ),
            ToolArgument(
                name="b",
                type="float",
                description="Second addend.",
                required=True,
            ),
        ],
    ),
    "time.now": ToolDefinition(
        name="time.now",
        description="Returns the current timestamp in ISO 8601 format.",
    ),
}


PROMPTS: Dict[str, Prompt] = {
    "summarize-resource": Prompt(
        name="summarize-resource",
        description="Summarize a resource for a customer-facing answer.",
        template=(
            "You are preparing a short summary for a customer question.\n"
            "Resource details:\n{resource_json}\n"
            "User question:\n{question}\n"
            "Provide a concise response."
        ),
        input_variables=["resource_json", "question"],
    ),
    "support-reply": Prompt(
        name="support-reply",
        description="Craft a polite support response using provided context.",
        template=(
            "Customer message:\n{customer_message}\n\n"
            "Context snippets:\n{context}\n\n"
            "Compose a supportive reply with next steps."
        ),
        input_variables=["customer_message", "context"],
    ),
}


def list_resources() -> list[Resource]:
    return list(RESOURCE_STORE.values())


def get_resource(resource_id: str) -> Resource | None:
    return RESOURCE_STORE.get(resource_id)


def list_tools() -> list[ToolDefinition]:
    return list(TOOL_DEFINITIONS.values())


def invoke_tool(tool_name: str, arguments: Dict[str, Any]) -> ToolInvocationResponse:
    if tool_name not in TOOL_DEFINITIONS:
        raise ValueError(f"Unknown tool: {tool_name}")

    if tool_name == "math.add":
        try:
            a = float(arguments.get("a"))
            b = float(arguments.get("b"))
        except (TypeError, ValueError):
            raise ValueError("Arguments 'a' and 'b' must be numbers.")
        return ToolInvocationResponse(output=a + b)

    if tool_name == "time.now":
        now = datetime.utcnow().isoformat() + "Z"
        return ToolInvocationResponse(output=now)

    raise ValueError(f"Execution not implemented for tool: {tool_name}")


def list_prompts() -> list[Prompt]:
    return list(PROMPTS.values())


def render_prompt(prompt_name: str, inputs: Dict[str, Any]) -> PromptRenderResponse:
    prompt = PROMPTS.get(prompt_name)
    if not prompt:
        raise ValueError(f"Unknown prompt: {prompt_name}")
    missing = [var for var in prompt.input_variables if var not in inputs]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Missing prompt inputs: {missing_list}")
    content = prompt.template.format(**inputs)
    return PromptRenderResponse(content=content, metadata={"prompt": prompt.name})
