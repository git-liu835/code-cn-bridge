"""DeepSeek 适配器"""

from __future__ import annotations

import json

from .base import BaseAdapter


class DeepSeekAdapter(BaseAdapter):
    name = "deepseek"
    base_url = "https://api.deepseek.com"
    api_key_env = "DEEPSEEK_API_KEY"

    def preprocess_chat_request(self, chat_req: dict) -> dict:
        # DeepSeek 不支持 logprobs
        chat_req.pop("logprobs", None)
        chat_req.pop("logit_bias", None)
        chat_req.pop("user", None)

        # stop 只支持单个字符串或字符串列表，DeepSeek 支持列表
        stop = chat_req.get("stop")
        if isinstance(stop, list) and len(stop) > 4:
            chat_req["stop"] = stop[:4]

        # 强制禁用 thinking 模式，避免模型进入思考循环
        # reasoning_content 会导致 code CLI 长时间转圈和反复执行相同命令
        if "thinking" not in chat_req:
            chat_req["thinking"] = {"type": "disabled"}

        # DeepSeek 对 tool 格式有要求，确保 function 字段存在
        tools = chat_req.get("tools")
        if tools:
            for tool in tools:
                if "function" not in tool and "name" in tool:
                    tool["function"] = {
                        "name": tool.pop("name"),
                        "description": tool.pop("description", ""),
                        "parameters": tool.pop("parameters", {}),
                    }
                if "type" not in tool:
                    tool["type"] = "function"
                # 修复 parameters: 必须是 type: "object" 的 JSON Schema
                params = tool.get("function", {}).get("parameters")
                if not params or not isinstance(params, dict):
                    tool.setdefault("function", {})["parameters"] = {"type": "object", "properties": {}}
                elif params.get("type") != "object":
                    params["type"] = "object"
                    params.setdefault("properties", {})

        return chat_req

    def postprocess_chat_response(self, chat_resp: dict) -> dict:
        """处理 DeepSeek 非流式响应"""
        choices = chat_resp.get("choices", [])
        for choice in choices:
            msg = choice.get("message", {})
            tool_calls = msg.get("tool_calls") or []
            for tc in tool_calls:
                if "type" not in tc:
                    tc["type"] = "function"
                func = tc.get("function", {})
                if "arguments" in func and isinstance(func["arguments"], dict):
                    func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)

        return chat_resp

    def stream_event_transform(self, raw_event: dict) -> dict:
        """DeepSeek SSE 格式基本标准，做微调"""
        for choice in raw_event.get("choices", []):
            delta = choice.get("delta", {})
            tool_calls = delta.get("tool_calls", [])
            for tc in tool_calls:
                if "type" not in tc:
                    tc["type"] = "function"
                func = tc.get("function", {})
                if "arguments" in func and isinstance(func["arguments"], dict):
                    func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)

        return raw_event

    def extract_tool_calls_from_content(self, content: str) -> list[dict] | None:
        return None  # DeepSeek 原生支持 tool_calls，无需提取
