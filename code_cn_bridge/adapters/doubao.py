"""豆包 (Doubao) 适配器 —— 火山引擎 Ark API

Chat:   POST /api/v3/chat/completions  (OpenAI 兼容)
Images: POST /api/v3/images/generations (DALL-E 兼容，支持 Seedream 扩展参数)
"""

from __future__ import annotations

import json

from .base import BaseAdapter


class DoubaoAdapter(BaseAdapter):
    name = "doubao"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    api_key_env = "ARK_API_KEY"

    def preprocess_image_gen_request(self, req: dict) -> dict:
        """DALL-E 兼容格式 + Seedream 扩展参数

        教程中的 extra_body 参数 (negative_prompt/cfg_scale/steps/watermark)
        会作为顶层字段透传，火山方舟 Ark API 支持这种 DALL-E 扩展格式。
        """
        # 确保必要字段
        req.setdefault("response_format", "url")
        # watermark: 免费默认 True，用户可设 False
        if "watermark" not in req:
            req["watermark"] = False
        return req

    # build_image_gen_url() 使用基类默认实现:
    #   {base_url}/images/generations → https://ark.cn-beijing.volces.com/api/v3/images/generations
    # 与官方教程一致

    def preprocess_chat_request(self, chat_req: dict) -> dict:
        # 移除不支持的字段
        chat_req.pop("logprobs", None)
        chat_req.pop("logit_bias", None)
        chat_req.pop("user", None)

        # stop 限制
        stop = chat_req.get("stop")
        if isinstance(stop, list) and len(stop) > 4:
            chat_req["stop"] = stop[:4]

        # 工具格式规范化
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
                # parameters 修复
                params = tool.get("function", {}).get("parameters")
                if not params or not isinstance(params, dict):
                    tool.setdefault("function", {})["parameters"] = {"type": "object", "properties": {}}
                elif params.get("type") != "object":
                    params["type"] = "object"
                    params.setdefault("properties", {})

        return chat_req

    def postprocess_chat_response(self, chat_resp: dict) -> dict:
        """处理豆包非流式响应"""
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
        """豆包 SSE 格式标准化"""
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
