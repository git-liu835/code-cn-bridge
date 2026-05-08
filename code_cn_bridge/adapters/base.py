"""适配器基类 —— 定义国产模型适配器的抽象接口"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """国产模型适配器基类

    子类必须设置:
      - name: 适配器名称 (如 "qwen", "deepseek")
      - base_url: 模型 API 基地址
      - api_key_env: API Key 对应的环境变量名
    """

    name: str = ""
    base_url: str = ""
    api_key_env: str = ""

    # ── 三个钩子方法 ─────────────────────────────────────────────

    def preprocess_chat_request(self, chat_req: dict) -> dict:
        """请求体微调 —— 在发送给上游模型之前调用

        可用于移除不支持的字段、调整参数格式等。
        """
        return chat_req

    def postprocess_chat_response(self, chat_resp: dict) -> dict:
        """非流式响应微调 —— 在协议转换之前调用

        可用于修复字段结构、提取异常位置的 tool_calls 等。
        """
        return chat_resp

    def stream_event_transform(self, raw_event: dict) -> dict:
        """单个 SSE chunk 结构调整 —— 在流式转换前调用

        不同模型返回的 SSE 事件结构可能不同，
        此方法负责统一为标准的 Chat Completions chunk 格式。

        标准格式应为:
          {"choices": [{"index": 0, "delta": {...}, "finish_reason": ...}]}
        """
        return raw_event

    # ── 工具调用相关 ─────────────────────────────────────────────

    def supports_tool_calls(self) -> bool:
        """是否原生支持 function calling"""
        return True

    def extract_tool_calls_from_content(self, content: str) -> list[dict] | None:
        """尝试从 message.content 文本中提取 tool_calls"""
        return None

    # ── 工具方法 ─────────────────────────────────────────────────

    def get_headers(self, api_key: str) -> dict:
        """构建请求头（子类可覆盖以适配不同认证方式）"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def build_chat_url(self) -> str:
        """构建 Chat Completions API URL"""
        base = self.base_url.rstrip("/")
        return f"{base}/chat/completions"

    def build_image_gen_url(self) -> str:
        """构建 Image Generation API URL（DALL-E 兼容格式）"""
        base = self.base_url.rstrip("/")
        return f"{base}/images/generations"

    def preprocess_image_gen_request(self, req: dict) -> dict:
        """生图请求预处理 —— 子类可覆盖以适配不同生图 API 格式"""
        return req
