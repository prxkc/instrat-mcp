from __future__ import annotations

from pathlib import Path
from typing import Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import settings
from .llm import build_llm_client
from .mcp import (
    get_resource,
    invoke_tool,
    list_prompts,
    list_resources,
    list_tools,
    render_prompt,
)
from .models import (
    ChatRequest,
    ChatResponse,
    Prompt,
    PromptRenderRequest,
    PromptRenderResponse,
    Resource,
    ToolDefinition,
    ToolInvocationRequest,
    ToolInvocationResponse,
)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LLM_CLIENT = build_llm_client()
FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "index.html"


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/mcp/resources", response_model=List[Resource])
async def resources() -> List[Resource]:
    return list_resources()


@app.get("/mcp/resources/{resource_id}", response_model=Resource)
async def resource_detail(resource_id: str) -> Resource:
    resource = get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
    return resource


@app.get("/mcp/tools", response_model=List[ToolDefinition])
async def tools() -> List[ToolDefinition]:
    return list_tools()


@app.post("/mcp/tools/invoke", response_model=ToolInvocationResponse)
async def tools_invoke(request: ToolInvocationRequest) -> ToolInvocationResponse:
    try:
        return invoke_tool(request.tool_name, request.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/mcp/prompts", response_model=List[Prompt])
async def prompts() -> List[Prompt]:
    return list_prompts()


@app.post("/mcp/prompts/render", response_model=PromptRenderResponse)
async def prompts_render(request: PromptRenderRequest) -> PromptRenderResponse:
    try:
        return render_prompt(request.prompt_name, request.inputs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/mcp/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    context_sections: list[str] = []
    details: dict[str, Any] = {"resources": [], "tools": []}

    for resource_id in request.context_resources:
        resource = get_resource(resource_id)
        if resource:
            context_sections.append(f"Resource {resource.title}:\n{resource.data}")
            details["resources"].append(resource.model_dump())

    tool_results = []
    for call in request.tool_calls:
        try:
            result = invoke_tool(call.tool_name, call.arguments)
            tool_results.append(result.output)
            details["tools"].append(
                {"name": call.tool_name, "arguments": call.arguments, "output": result.output}
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    prompt_content = None
    if request.prompt_name:
        try:
            rendered = render_prompt(request.prompt_name, request.prompt_inputs)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        prompt_content = rendered.content
        details["prompt"] = {
            "name": request.prompt_name,
            "inputs": request.prompt_inputs,
            "content": prompt_content,
        }

    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant connected to an MCP demo server. "
                "Use provided context to craft practical answers."
            ),
        }
    ]

    if prompt_content:
        messages.append({"role": "system", "content": prompt_content})

    if context_sections:
        context_block = "\n\n".join(context_sections)
        messages.append({"role": "system", "content": f"Context snippets:\n{context_block}"})

    if tool_results:
        tool_block = "\n".join(str(out) for out in tool_results)
        messages.append({"role": "system", "content": f"Tool outputs:\n{tool_block}"})

    messages.append({"role": "user", "content": request.message})

    try:
        completion, meta = await LLM_CLIENT.generate(messages)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=f"LLM interaction failed: {exc}",
        ) from exc

    details["llm_meta"] = meta

    return ChatResponse(
        message=completion,
        provider=LLM_CLIENT.provider,
        mock=LLM_CLIENT.mock,
        details=details,
    )


@app.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="Frontend index not found.")
    return FileResponse(FRONTEND_INDEX)
