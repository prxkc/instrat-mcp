from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Resource(BaseModel):
    id: str
    title: str
    description: str
    uri: str
    mime_type: str
    tags: list[str] = Field(default_factory=list)
    data: dict[str, Any]


class ToolArgument(BaseModel):
    name: str
    type: str
    description: str
    required: bool = False


class ToolDefinition(BaseModel):
    name: str
    description: str
    arguments: list[ToolArgument] = Field(default_factory=list)


class ToolInvocationRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolInvocationResponse(BaseModel):
    output: Any
    metadata: dict[str, Any] = Field(default_factory=dict)


class Prompt(BaseModel):
    name: str
    description: str
    template: str
    input_variables: list[str] = Field(default_factory=list)


class PromptRenderRequest(BaseModel):
    prompt_name: str
    inputs: dict[str, Any] = Field(default_factory=dict)


class PromptRenderResponse(BaseModel):
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    context_resources: list[str] = Field(default_factory=list)
    tool_calls: list[ToolInvocationRequest] = Field(default_factory=list)
    prompt_name: str | None = None
    prompt_inputs: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    message: str
    provider: str
    mock: bool = False
    details: dict[str, Any] = Field(default_factory=dict)
