# code CN Bridge 产品需求文档 (PRD)

| 文档版本 | 1.0            |
| -------- | -------------- |
| 作者     | 高级算法工程师 |
| 日期     | 2026-05-07     |
| 状态     | 待开发         |

------

## 1. 产品概述

### 1.1 背景

OpenAI code CLI (v0.8.0+) 默认使用 `/v1/responses` API 端点进行交互，而几乎所有国内大语言模型（通义千问、DeepSeek、Kimi 等）仅提供 `/v1/chat/completions` 兼容接口。协议差异导致无法直接使用最新版 code 的全部高级功能（Skills、Sandbox、MCP 工具调用等）。用户需要一个轻量级中间件，实现协议透明转换，使 code 能够无缝接入国内模型。

### 1.2 产品目标

开发一个名为 **code CN Bridge** 的本地代理工具，实现以下目标：

- **一键部署**：用户通过 `pip install` 或 Docker 快速启动。
- **完整协议兼容**：支持 code CLI 最新版的全部功能，包括多轮 Agent 循环、工具调用、流式输出。
- **多模型支持**：通过插件式适配器兼容主流国产大模型。
- **零配置侵入**：用户仅需设置 `OPENAI_BASE_URL` 环境变量指向该代理。

### 1.3 目标用户

- 希望使用国产大模型驱动 code CLI 的开发者。
- 需要私有化部署、控制数据出境的团队。
- 对 code Agent 能力有深度使用需求的工程师。

------

## 2. 用户故事

- **作为开发者**，我希望在终端运行 `codex` 时，能通过配置好的国内 API Key 使用通义千问/DeepSeek 等模型，并获得与官方 OpenAI 模型一致的 Agent 体验。
- **作为开发团队 LEAD**，我希望部署一个本地服务，统一管理多个成员的 API Key 和模型路由，并监控用量。
- **作为开源社区贡献者**，我希望为新的国产模型添加适配器时，只需实现简单接口，无需修改核心转换逻辑。

------

## 3. 功能需求

### 3.1 核心转换引擎

- **请求转换**：将 code 发出的 OpenAI Responses API 格式请求转换为 Chat Completions API 请求。
  - 映射 `input` 数组 → `messages` 数组。
  - 映射 `tools` 定义，确保每个 tool 对象包含 `type: "function"`（若缺失则自动补充）。
  - 映射 `max_output_tokens` → `max_tokens`。
  - 处理 `tool_choice`、`temperature`、`stop` 等参数。
- **响应转换**：将 Chat Completions 响应（非流式）转换为 Responses API 格式。
  - 提取 `choices[0].message`，构造 `output` 数组，包含 `message` 或 `function_call` 类型的输出项。
  - 为每个输出项生成唯一 ID，为整个响应生成 `response_id`。
- **流式转换**：将 Chat Completions 的 SSE 流实时转换为 Responses API 的流式事件。
  - 支持增量文本 (`output_text.delta`)。
  - 支持增量工具调用 (`function_call` 增量聚合并最终发出)。
  - 正确处理 `response.created`、`response.completed` 等生命周期事件。

### 3.2 多模型适配器

- 提供抽象基类 `BaseAdapter`，定义以下钩子：
  - `preprocess_chat_request(chat_req: dict) -> dict`：请求体微调。
  - `postprocess_chat_response(chat_resp: dict) -> dict`：非流式响应微调。
  - `stream_event_transform(chunk: dict) -> dict`：单个 SSE chunk 字段/结构调整。
- 内置适配器：
  - **通义千问 (Qwen)**：处理 `output.choices` 字段重命名，从 content 中提取遗漏的 tool_calls。
  - **DeepSeek**：处理 `stop` 参数限制，关闭不支持的 `logprobs`。
  - **Moonshot (Kimi)**：老版本降级处理，禁用 function calling 时通过提示词引导。
- 适配器注册与动态加载机制。

### 3.3 工具调用 (Function Calling) 全兼容

- 请求侧：确保 `tools` 数组每个元素结构为 `{"type":"function", "function": {"name":"...", "parameters":{...}}}`。
- 响应侧：国产模型可能将 tool_calls 放在 `message.content` 而非标准的 `tool_calls` 字段中。代理必须检测并提取，重新组装为标准 `tool_calls`。
- 多工具并行调用时，生成多个 `function_call` 输出项，保持 `call_id` 唯一且对应。

### 3.4 高级功能保障

- **Skills**：系统提示词和动态上下文完全透传，无需修改。
- **Sandbox 代码执行**：作为普通工具调用处理，代理无需感知执行逻辑，只需确保 tool_call 正确转换。
- **MCP 工具**：工具定义同样通过 `tools` 传递，适配器无额外工作。
- **多轮对话与 Agent 循环**：通过生成和维护 `response_id` 和 `previous_response_id` 保持上下文连续性。

### 3.5 配置管理

- 支持 YAML 配置文件（默认路径：`~/.code-cn-bridge.yaml`）。
- 支持通过环境变量注入 API Key（如 `QWEN_API_KEY`、`DEEPSEEK_API_KEY`）。
- 支持模型名别名映射：`codex-model-name` → `qwen-plus` 等。
- 热加载配置（监听文件变更或手动触发 API）。

### 3.6 部署与分发

- **PyPI 包**：提供 `code-cn-bridge` 包，安装后通过命令行快速启动。
- **Docker 镜像**：提供可直接运行的容器镜像。
- 一键启动脚本，自动检查环境并生成默认配置。

------

## 4. 非功能需求

### 4.1 性能

- 代理本身引入的延迟 < 50ms（p50）。
- 支持至少 10 个并发流式连接不阻塞。
- 流式转换内存占用稳定，无大缓存。

### 4.2 可靠性

- 异常时向 code 返回符合 OpenAI 格式的错误响应（如 `{"error": {"message": "..."}}`），不导致 code 崩溃。
- 网络中断时正确清理上游连接。

### 4.3 安全性

- API Key 仅在内存中处理，不写入日志或响应。
- 代理仅监听 `127.0.0.1`，不对外暴露。
- 可选：支持请求审计日志，但默认关闭。

### 4.4 可扩展性

- 新增国产模型适配器通过 Python 类继承实现，无需修改核心代码。
- 支持通过插件目录自动发现适配器。

### 4.5 易用性

- 首次运行生成示例配置文件并给出引导说明。
- 提供 `--verbose` 模式打印请求/响应摘要用于调试。

------

## 5. 技术架构

### 5.1 整体架构图

text

```
┌─────────────┐       HTTP (localhost:8765)       ┌─────────────────────┐       HTTPS       ┌──────────────┐
│  code CLI   │ ────────────────────────────────▶ │  code CN Bridge     │ ────────────────▶ │  Qwen API    │
│  (Responses) │ ◀──────────────────────────────── │  (FastAPI + httpx)   │ ◀──────────────── │  (Chat API)  │
└─────────────┘                                   └─────────────────────┘                   └──────────────┘
                                                       │    ▲
                                                       │    │
                                                       ▼    │
                                                ┌──────────────┐
                                                │  适配器注册表  │
                                                └──────────────┘
```

### 5.2 核心组件

| 组件                    | 职责                                                         |
| ----------------------- | ------------------------------------------------------------ |
| **FastAPI 服务器**      | 提供 `/v1/responses` 和 `/v1/chat/completions` 端点，接收 code 请求 |
| **Protocol Translator** | 负责 Responses ↔ Chat 的双向映射，包括流式转换               |
| **Adapter Registry**    | 管理模型名到适配器实例的映射                                 |
| **HTTP Client (httpx)** | 异步转发请求到国产模型 API                                   |
| **Config Loader**       | 读取 YAML 配置和环境变量，支持热加载                         |

### 5.3 数据流

1. code 发送 POST 请求到 `http://localhost:8765/v1/responses`。
2. FastAPI 路由接收 JSON body，提取 `model` 字段。
3. 根据模型名查找对应的适配器，通过 `preprocess` 钩子微调请求参数。
4. `Protocol Translator` 将 Responses 请求转换为 Chat 请求体。
5. 使用 httpx 异步客户端将请求转发到目标模型的 `/v1/chat/completions`。
6. 若 `stream=true`，则读取上游 SSE 流，逐事件经 `stream_event_transform` 后，由转换器包装为 Responses 格式的 SSE，流式返回给 code。
7. 若非流式，则接收完整 JSON 响应，经适配器 `postprocess` 后，由转换器构建 Responses 响应返回。
8. 错误情况直接构造 OpenAI 兼容错误响应。

------

## 6. API 接口详细设计

### 6.1 代理端点：`POST /v1/responses`

**请求示例** (code 发出)：

json

```
{
  "model": "gpt-5-code",
  "input": [
    {"role": "system", "content": "You are an expert..."},
    {"role": "user", "content": "Write a function..."}
  ],
  "tools": [
    {"type": "function", "name": "run_python", "parameters": {...}}
  ],
  "tool_choice": "auto",
  "stream": true,
  "max_output_tokens": 4096
}
```

**代理内部转换后转发给国内模型**：

json

```
{
  "model": "qwen-plus",
  "messages": [
    {"role": "system", "content": "You are an expert..."},
    {"role": "user", "content": "Write a function..."}
  ],
  "tools": [{"type": "function", "function": {"name": "run_python", "parameters": {...}}}],
  "stream": true,
  "max_tokens": 4096
}
```

**上游模型返回示例（Chat SSE chunk）**：

text

```
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"name":"run_python","arguments":"import"}}]}}]}
```

**代理转换为 Responses 流式事件**：

text

```
data: {"id":"resp_abc123","object":"response.output_item.added","output_index":0,"item":{"id":"func_xyz","type":"function_call","name":"run_python","status":"in_progress"}}

data: {"id":"resp_abc123","object":"response.function_call_arguments.delta","delta":"import"}

data: {"id":"resp_abc123","object":"response.completed","output":[...]}
```

### 6.2 辅助端点：`POST /v1/chat/completions`

（为兼容部分旧版 code 配置或直接测试，可选择实现透传）

**实现**：接收标准 Chat 请求，通过适配器微调后直接转发，响应也直接透传，不进行协议转换。

### 6.3 管理端点（可选）

- `GET /health`：返回 `{"status": "ok", "models": [...]}`。
- `POST /admin/reload-config`：热加载配置文件。

------

## 7. 适配器规范

### 7.1 基类定义

python

```
class BaseAdapter(ABC):
    """国产模型适配器基类"""
    
    # 必填：模型API基地址
    base_url: str
    # 必填：API Key 环境变量名或直接值
    api_key_env: str
    
    # 请求预处理（默认不处理）
    def preprocess_chat_request(self, chat_req: dict) -> dict:
        return chat_req
    
    # 非流式响应后处理（默认不处理）
    def postprocess_chat_response(self, chat_resp: dict) -> dict:
        return chat_resp
    
    # 单个 SSE chunk 转换（用于修正字段差异）
    def stream_event_transform(self, raw_event: dict) -> dict:
        # 默认返回原事件
        return raw_event
```

### 7.2 示例：通义千问适配器

- **preprocess**：移除不支持的 `stop` 列表格式（若存在）。
- **postprocess**：检测 `choices[0].message.content` 中是否包含类似 `<tool_call>` 的 JSON，若有，提取并构建标准 `tool_calls`，清空 `content`。
- **stream_event_transform**：千问的 SSE 事件体可能为 `{"output": {"choices": [...]}}`，需提取 `output.choices` 赋给根节点 `choices`。

### 7.3 添加新适配器步骤

1. 继承 `BaseAdapter`，实现必要方法。
2. 在适配器注册表中添加模型名与适配器类的映射。
3. 更新配置文件示例。

------

## 8. 配置规范

### 8.1 配置文件 `~/.code-cn-bridge.yaml`

yaml

```
server:
  host: 127.0.0.1
  port: 8765

providers:
  qwen:
    adapter: qwen
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key_env: QWEN_API_KEY
  deepseek:
    adapter: deepseek
    base_url: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY

model_mapping:
  # code 请求中的模型名 → 国内模型名
  "gpt-5-code": "qwen-plus"    # 或者 "deepseek-chat"
  "gpt-5-code-light": "qwen-turbo"
```

### 8.2 环境变量

代理启动时读取对应 `api_key_env` 的环境变量，未找到则报错退出。

------

## 9. 部署指南

### 9.1 pip 安装

bash

```
pip install code-cn-bridge
code-cn-bridge init --provider qwen --api-key $QWEN_API_KEY
code-cn-bridge start
```

然后设置 code 环境变量：

bash

```
export OPENAI_BASE_URL="http://localhost:8765/v1"
export OPENAI_API_KEY="any-value"
```

### 9.2 Docker 部署

bash

```
docker run -d -p 8765:8765 \
  -e QWEN_API_KEY=xxx \
  -v $(pwd)/config.yaml:/app/config.yaml \
  your-registry/code-cn-bridge:latest
```

------

## 10. 开发里程碑

| 阶段 | 内容                              | 产出                                | 预计时间 |
| ---- | --------------------------------- | ----------------------------------- | -------- |
| M1   | 基础框架 + 协议转换引擎（非流式） | 能启动的 FastAPI 服务，单次对话通过 | 2天      |
| M2   | 流式转换实现 + 通义千问适配器     | 完整的 Qwen 流式对话                | 2天      |
| M3   | 工具调用适配 + Sandbox 验证       | Qwen 的 Function Calling 完美运行   | 2天      |
| M4   | 多适配器支持 + DeepSeek 适配      | 可切换模型                          | 1天      |
| M5   | 配置管理、Docker 镜像、CLI 打包   | 发布 PyPI 版本和 Docker 镜像        | 1天      |
| M6   | 测试 + 文档 + 错误处理完善        | 用户可以直接使用的稳定版            | 2天      |

------

## 11. 风险与对策

| 风险                            | 影响                        | 对策                                                         |
| ------------------------------- | --------------------------- | ------------------------------------------------------------ |
| 国产模型 API 协议更新           | 适配器失效                  | 模块化设计，快速发布新适配器版本                             |
| 国产模型不支持 function calling | 无法使用 Sandbox 等高级功能 | 检测模型能力，降级为提示词引导或提示用户更换模型             |
| 流式转换中字段不一致            | code 解析报错              | 为每个模型编写详尽的 `stream_event_transform` 单元测试       |
| 代理自身性能瓶颈                | 增加显著延迟                | 使用全异步 I/O，选择高性能 Web 服务器（uvicorn），必要时引入缓存 |

------

## 12. 附录：协议映射示例

**code Responses 请求 → 千问 Chat 请求** 对照表：

| Responses 字段         | Chat 字段             | 转换规则                          |
| ---------------------- | --------------------- | --------------------------------- |
| `input` (数组)         | `messages`            | 原样传递                          |
| `tools`                | `tools`               | 确保每个元素有 `type: "function"` |
| `tool_choice: "auto"`  | `tool_choice: "auto"` | 保留                              |
| `max_output_tokens: N` | `max_tokens: N`       | 直接映射                          |
| `stream: true`         | `stream: true`        | 保留                              |
| `temperature`          | `temperature`         | 保留                              |
| `previous_response_id` | ——                    | 无关，不传递                      |

**千问 Chat 流式响应 → Codex Responses 流式事件**：

| 千问 SSE 字段 `output.choices[0].delta` | code Responses 事件                     | 处理                       |
| --------------------------------------- | ---------------------------------------- | -------------------------- |
| `content: "text"`                       | `response.output_text.delta`             | 发送文本增量               |
| `tool_calls[0].function.name`           | `response.output_item.added`             | 发送新增函数调用 item      |
| `tool_calls[0].function.arguments` 增量 | `response.function_call_arguments.delta` | 发送参数增量               |
| 最终 `finish_reason: "tool_calls"`      | `response.completed`                     | 汇总 output 并发送完成事件 |