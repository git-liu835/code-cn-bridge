"""中间件 —— 错误处理、请求日志、API Key 安全过滤"""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .models import build_error_response

logger = logging.getLogger("code-cn-bridge")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """统一错误处理中间件"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception("未处理的异常: %s", exc)
            return JSONResponse(
                content=build_error_response(str(exc)),
                status_code=500,
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件（不记录 API Key）"""

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()

        # 跳过健康检查日志
        if request.url.path == "/health":
            return await call_next(request)

        logger.info("→ %s %s", request.method, request.url.path)

        response = await call_next(request)

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            "← %s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


class ApiKeyFilter(logging.Filter):
    """过滤日志中的 API Key"""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args and isinstance(record.args, dict):
            record.args = {
                k: ("***" if "key" in k.lower() or "token" in k.lower() else v)
                for k, v in record.args.items()
            }
        return True
