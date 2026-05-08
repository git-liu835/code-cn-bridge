# code CN Bridge

本地代理工具，将 OpenAI Responses API 翻译为 Chat Completions API，使 code CLI 无缝接入通义千问、DeepSeek、Kimi 等国产大模型。

**v2.0** 新增原生桌面管理界面（Electron + React），无需编辑 YAML 或打开浏览器。

## 两种使用方式

### 方式一：桌面安装包（推荐）

从 [Releases](https://github.com/git-liu835/code-cn-bridge/releases) 页面下载对应平台的安装包安装，双击启动即可：

| 平台 | 安装包 |
|------|--------|
| Windows | `code-CN-Bridge-Setup-0.1.0.exe` |
| macOS | `code-CN-Bridge-0.1.0.dmg` |
| Linux | `code-CN-Bridge-0.1.0.AppImage` |

安装后：打开软件 → 配置模型和 API Key → 点击启动 → 完成。无需安装 Python 环境。

配置 code CLI 连接代理：
```bash
export OPENAI_BASE_URL="http://localhost:8765/v1"
export OPENAI_API_KEY="any-value"
```

### 方式二：源码运行

适合开发者，直接 clone 源码运行：

```bash
# 1. 克隆
git clone https://github.com/git-liu835/code-cn-bridge.git
cd code-cn-bridge

# 2. 安装 Python 依赖
pip install -e .

# 3. 配置 API Key（复制模板并填入真实 key）
cp example.env .env
# 编辑 .env 填入你的 API 密钥

# 4. 启动桌面应用（需要 Node.js）
cd desktop && npm install && npm run electron:dev

# 或者纯命令行模式
code-cn-bridge start
```

关闭主窗口后，代理继续在系统托盘运行。

## 快速开始（命令行版）

```bash
code-cn-bridge init --provider qwen
export QWEN_API_KEY="your-api-key"
code-cn-bridge start
```

## 配置

配置文件默认路径：`~/.code-cn-bridge.yaml`（CLI 和桌面版共用）

```yaml
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
  "gpt-5-code": "qwen-plus"
  "gpt-5-code-light": "qwen-turbo"
```

## 支持的模型

| 模型       | 适配器   | 功能调用 | 流式输出 |
| --------- | -------- | ------- | ------- |
| 通义千问   | qwen     | ✅      | ✅      |
| DeepSeek  | deepseek | ✅      | ✅      |
| Kimi      | kimi     | ✅      | ✅      |
| 豆包/火山  | doubao   | ✅      | ✅      |
| 智谱 GLM  | zhipu    | ✅      | ✅      |

## CLI 命令

```bash
code-cn-bridge start        # 启动代理
code-cn-bridge start -v     # 启动代理（调试模式）
code-cn-bridge init         # 初始化配置
code-cn-bridge validate     # 验证配置
code-cn-bridge list-adapters # 列出适配器
```

## 桌面应用功能

| 页面 | 功能 |
| ---- | ---- |
| 仪表板 | 代理状态、请求统计、模型健康卡片 |
| 模型配置 | 添加/编辑/删除模型、测试连接、高级选项 |
| 全局设置 | 端口、日志级别、配置导入/导出 |
| 监控日志 | 实时 WebSocket 推送、状态码、耗时、错误高亮 |
| 关于 | 版本信息、项目链接 |

## 管理 API

桌面应用通过以下端点控制代理（`localhost:8765/admin/api`）：

| 方法 | 路径 | 描述 |
| ---- | ---- | ---- |
| GET | `/status` | 代理运行状态 |
| GET/POST | `/models` | 模型列表/添加 |
| PUT/DELETE | `/models/{name}` | 更新/删除模型 |
| POST | `/models/{name}/test` | 测试连接 |
| GET/PUT | `/settings` | 全局设置 |
| GET | `/logs` | 请求日志 |
| WS | `/logs/stream` | 实时日志流 |
| GET | `/config/export` | 导出配置 |
| POST | `/config/import` | 导入配置 |
| POST | `/shutdown` | 安全关闭 |

## 架构

```
┌──────────────────────────────────────────────┐
│                   Electron 主进程             │
│  ┌───────────────────┐  ┌─────────────────┐  │
│  │  管理子进程        │  │ 系统托盘/窗口   │  │
│  │  (FastAPI 代理)    │  │                 │  │
│  └────────┬──────────┘  └─────────────────┘  │
│           │                                   │
│           ▼                                   │
│  ┌────────────────────┐                      │
│  │  React 前端 (UI)    │                      │
│  └────────────────────┘                      │
└──────────────────────────────────────────────┘
       │
       │ HTTP (localhost:8765)
       ▼
┌─────────────┐       HTTPS       ┌──────────────┐
│  code CLI   │ ────────────────▶ │  国产模型 API │
└─────────────┘                   └──────────────┘
```

## 构建发布包

```bash
# 一键构建所有平台的安装包
# Windows:
scripts\build-all.bat

# macOS / Linux:
bash scripts/build-all.sh
```

构建流程：PyInstaller 打包 Python 后端 → vite 打包 React 前端 → electron-builder 生成安装包

## License

MIT
