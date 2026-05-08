FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY codex_cn_bridge/ ./codex_cn_bridge/
COPY pyproject.toml .
COPY README.md .

# 安装包
RUN pip install --no-cache-dir -e .

# 默认配置文件
COPY config.yaml ./config.yaml

ENV PYTHONUNBUFFERED=1

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8765/health').raise_for_status()" || exit 1

ENTRYPOINT ["codex-cn-bridge"]
CMD ["start"]
