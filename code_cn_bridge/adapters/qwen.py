"""通义千问 (Qwen) 适配器"""

from __future__ import annotations

import json
import re

from .base import BaseAdapter


class QwenAdapter(BaseAdapter):
    name = "qwen"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key_env = "QWEN_API_KEY"

    def preprocess_chat_request(self, chat_req: dict) -> dict:
        # 移除千问不支持的字段
        chat_req.pop("logprobs", None)
        chat_req.pop("logit_bias", None)
        chat_req.pop("user", None)

        # stop 只支持字符串数组或单个字符串
        stop = chat_req.get("stop")
        if isinstance(stop, list):
            chat_req["stop"] = stop  # 千问支持列表
        return chat_req

    def postprocess_chat_response(self, chat_resp: dict) -> dict:
        """处理千问的非流式响应"""
        choices = chat_resp.get("choices", [])
        for choice in choices:
            msg = choice.get("message", {})
            content = msg.get("content", "")

            # 千问可能将 tool_calls 嵌套在 content 的 JSON 中
            if content and isinstance(content, str):
                extracted = self.extract_tool_calls_from_content(content)
                if extracted:
                    msg["tool_calls"] = extracted
                    msg["content"] = None  # 有 tool_calls 时 content 应为空

            # 确保 tool_calls 结构正确
            tool_calls = msg.get("tool_calls") or []
            for tc in tool_calls:
                if "type" not in tc:
                    tc["type"] = "function"
                func = tc.get("function", {})
                if "arguments" in func and isinstance(func["arguments"], dict):
                    func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)

        return chat_resp

    def stream_event_transform(self, raw_event: dict) -> dict:
        """千问 SSE 事件可能为 {"output": {"choices": [...]}} 格式"""
        # 提取 output.choices
        if "output" in raw_event and "choices" not in raw_event:
            output = raw_event["output"]
            if isinstance(output, dict) and "choices" in output:
                raw_event["choices"] = output["choices"]

        # 确保 choices 存在
        if "choices" not in raw_event:
            return raw_event

        for choice in raw_event.get("choices", []):
            delta = choice.get("delta", {})
            tool_calls = delta.get("tool_calls", [])

            # 确保 tool_call 有 type
            for tc in tool_calls:
                if "type" not in tc:
                    tc["type"] = "function"
                func = tc.get("function", {})
                # arguments 可能是 dict
                if "arguments" in func and isinstance(func["arguments"], dict):
                    func["arguments"] = json.dumps(func["arguments"], ensure_ascii=False)

        return raw_event

    def extract_tool_calls_from_content(self, content: str) -> list[dict] | None:
        """从 content 中提取 tool_calls (千问旧版可能把 tool_call 放在 content 里)"""
        if not content:
            return None

        # 尝试匹配 <tool_call>{"name": "...", "arguments": {...}}</tool_call>
        pattern = r"<tool_call>\s*(.*?)\s*</tool_call>"
        matches = re.findall(pattern, content, re.DOTALL)
        if not matches:
            return None

        tool_calls = []
        for i, m in enumerate(matches):
            try:
                data = json.loads(m)
                tool_calls.append({
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": data.get("name", ""),
                        "arguments": json.dumps(data.get("arguments", {}), ensure_ascii=False),
                    },
                })
            except json.JSONDecodeError:
                # 尝试函数调用格式
                fn_match = re.match(
                    r'(\w+)\s*\((.*)\)', m.strip(), re.DOTALL
                )
                if fn_match:
                    tool_calls.append({
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": fn_match.group(1),
                            "arguments": fn_match.group(2).strip(),
                        },
                    })

        return tool_calls if tool_calls else None
