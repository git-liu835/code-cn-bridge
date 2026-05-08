"""Pydantic 数据模型 —— 定义 Responses API 和 Chat Completions API 的结构"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


# ── Chat Completions API 模型 ──────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str | list[dict] | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ChatFunctionDef(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None


class ChatToolDef(BaseModel):
    type: Literal["function"] = "function"
    function: ChatFunctionDef


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stop: str | list[str] | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict | None = None


# ── Responses API 模型 ─────────────────────────────────────────────

class ResponsesInputItem(BaseModel):
    role: str
    content: str | list[dict] | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ResponsesRequest(BaseModel):
    model: str
    input: list[dict[str, Any]] = Field(default_factory=list)
    instructions: str | None = None
    max_output_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stop: str | list[str] | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict | None = "auto"
    previous_response_id: str | None = None
    metadata: dict[str, Any] | None = None


# ── Responses API 输出项 ───────────────────────────────────────────

def make_output_text(text: str) -> dict:
    return {"type": "output_text", "text": text, "annotations": []}


def make_message_output_item(content_text: str) -> dict:
    item_id = _uid("msg")
    return {
        "id": item_id,
        "object": "realtime.item",
        "type": "message",
        "role": "assistant",
        "status": "completed",
        "content": [make_output_text(content_text)],
    }


def make_function_call_output_item(name: str, arguments: str, call_id: str | None = None) -> dict:
    fc_id = call_id or _uid("call")
    item_id = _uid("func")
    return {
        "id": item_id,
        "object": "realtime.item",
        "type": "function_call",
        "name": name,
        "call_id": fc_id,
        "arguments": arguments,
        "status": "completed",
    }


# ── Responses API 非流式响应 ───────────────────────────────────────

def build_responses_response(
    output_items: list[dict],
    model: str,
    usage: dict | None = None,
) -> dict:
    return {
        "id": _uid("resp"),
        "object": "response",
        "status": "completed",
        "model": model,
        "output": output_items,
        "usage": usage or {},
    }


# ── 错误响应 ───────────────────────────────────────────────────────

def build_error_response(message: str, code: str = "internal_error", status_code: int = 500) -> dict:
    return {
        "error": {
            "message": message,
            "type": code,
            "code": status_code,
        },
    }
