# Personal AI Agent Framework — 架构文档

## 1. 概述

**Personal AI Agent Framework** 是一个轻量级、模块化、可扩展的 AI Agent 框架模板。它的核心理念是 **"技能即插件"** —— 你只需要在 `skills/` 目录下创建一个 `.py` 文件，Agent 就会自动发现并使用它，**无需修改任何核心代码**。

### 设计哲学

| 原则 | 说明 |
|------|------|
| **零配置扩展** | 新增技能 = 新建一个 `.py` 文件，自动注册 |
| **框架与功能分离** | `core/` 只做调度，`skills/` 只做执行 |
| **显式优于隐式** | 每个技能必须声明 `name`、`description`、`keywords` |
| **约定优于配置** | 目录结构即注册表，无需 YAML/JSON 配置文件 |
| **可替换性** | Memory、Router、配置都可通过接口替换 |

---

## 2. 项目结构

```
personal agentV1/
│
├── main.py                      # 入口：启动 Agent
├── config.py                    # 配置：AgentConfig 数据类
│
├── core/                        # 框架内核 —— 不应该频繁修改
│   ├── __init__.py
│   ├── agent.py                 # Agent 核心：生命周期 + REPL 循环
│   ├── router.py                # Router：关键词 + LLM 混合路由
│   └── memory.py                # MemoryStore：对话历史 + 用户画像
│
├── skills/                      # 技能插件 —— 扩展点
│   ├── __init__.py
│   ├── base.py                  # BaseSkill 抽象基类 + SkillResult
│   ├── registry.py              # SkillRegistry：自动发现
│   ├── chat.py                  # ChatSkill：通用对话（默认后备）
│   └── game_generator.py        # GameGeneratorSkill：HTML5 游戏生成
│
├── tools/                       # 工具库 —— 供技能调用
│   ├── __init__.py
│   ├── base.py                  # BaseTool 抽象基类
│   ├── registry.py              # ToolRegistry：自动发现
│   ├── browser_tool.py          # BrowserTool：在浏览器中打开文件
│   └── file_tool.py             # FileTool：写文件到磁盘
│
├── prompts/                     # 提示词模板
│   ├── system.txt               # 系统提示词（用 {name}{role} 等占位符）
│   └── game_prompt.txt          # 游戏生成专家提示词
│
├── memory/                      # 持久化数据
│   ├── user.json                # 用户画像
│   └── chat_history.json        # 对话历史（OpenAI 格式）
│
└── output/                      # 生成的输出文件
    └── game.html                # 游戏生成示例输出
```

---

## 3. 核心概念

### 3.1 架构全景图

```
┌─────────────────────────────────────────────────────────┐
│                       main.py                           │
│                   (启动、配置、退出)                      │
└───────────────────────┬─────────────────────────────────┘
                        │ 实例化
                        ▼
┌─────────────────────────────────────────────────────────┐
│                     Agent (核心)                         │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐   │
│  │  Memory  │   │  Router  │   │  SkillRegistry   │   │
│  │  Store   │   │          │   │                  │   │
│  │          │   │ 关键词匹配 │   │ chat             │   │
│  │ 对话历史  │   │   ↓      │   │ game_generator   │   │
│  │ 用户画像  │   │ LLM路由  │   │ weather (你的)   │   │
│  └──────────┘   └────┬─────┘   └────────┬─────────┘   │
│                      │                  │              │
│                      │  返回 skill 名称   │ 查找 skill   │
│                      ▼                  ▼              │
│                 Skill.execute(user_input, memory,      │
│                                tools, config)          │
│                         │                              │
│                         ▼                              │
│                  ┌──────────────┐                      │
│                  │ ToolRegistry │                      │
│                  │              │                      │
│                  │ file_tool    │                      │
│                  │ browser_tool │                      │
│                  └──────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Agent (`core/agent.py`)

Agent 是框架的**中心调度器**。它不执行任何具体业务逻辑，只负责编排：

- **启动时**：加载 Memory → 初始化 SkillRegistry → 初始化 ToolRegistry → 注入 LLM 客户端
- **运行时**：`用户输入 → Router 路由 → 查找 Skill → 执行 Skill → 展示结果`
- **关闭时**：保存 Memory → 清理资源

Agent 暴露了多个**可重写的钩子方法**，子类可以扩展：
- `_get_input()` — 自定义输入源（GUI、WebSocket、语音等）
- `_display_result()` — 自定义输出格式（Markdown、语音合成等）
- `_should_exit()` — 自定义退出条件
- `_on_startup()` / `_on_shutdown()` — 生命周期钩子

### 3.3 Skill 系统 (`skills/`)

#### BaseSkill — 技能基类

每个技能必须实现 4 个抽象成员：

```python
class MySkill(BaseSkill):
    name = "my_skill"                    # 唯一标识，用于路由
    description = "一句话描述这个技能做什么"
    keywords = ["关键词1", "关键词2"]      # 触发词列表

    def execute(self, user_input, memory, tools, config) -> SkillResult:
        # 你的业务逻辑
        return SkillResult(
            skill_name="my_skill",
            output="给用户看的文本",
            artifacts=["生成的/文件/路径"],   # 可选
            metadata={"key": "value"}        # 可选
        )
```

#### SkillResult

技能执行后返回的标准结果：

| 字段 | 类型 | 说明 |
|------|------|------|
| `skill_name` | `str` | 技能名称 |
| `output` | `str` | 展示给用户的文本 |
| `artifacts` | `List[str]` | 生成的文件路径列表 |
| `metadata` | `Dict` | 任意元数据 |

#### SkillRegistry — 自动发现

启动时，`SkillRegistry` 扫描 `skills/*.py`，使用 `importlib` 动态导入每个模块，然后用 `inspect.getmembers()` 找到所有 `BaseSkill` 的子类，自动实例化并注册。

**关键行为**：
- 跳过 `__init__.py`、`base.py`、`registry.py`
- 跳过没有 `BaseSkill` 子类的文件（打印警告）
- 同名技能后注册的会覆盖先注册的

### 3.4 Router — 混合路由 (`core/router.py`)

路由采用**两阶段策略**，兼顾速度和智能：

```
用户输入: "帮我做一个贪吃蛇游戏"
        │
        ▼
┌─────────────────────┐
│ Phase 1: 关键词匹配   │  遍历所有 Skill 的 keywords
│ (免费、快速)         │  计算 match_score
└─────────┬───────────┘
          │
    score >= 0.25? ─── Yes ──→ 直接路由到 game_generator
          │
          No
          │
          ▼
┌─────────────────────┐
│ Phase 2: LLM 路由    │  动态生成 Prompt 列出所有技能
│ (1次 API 调用)      │  让 LLM 决定最合适的技能
└─────────┬───────────┘
          │
    验证：结果是否在已知技能列表中？
          │
    Yes ──→ 路由到指定技能
    No  ──→ 回退到 "chat"
```

**为什么用混合路由？**
- 纯 LLM 路由每次用户输入都要调用 API（慢且贵）
- 纯关键词路由太死板（"搞个蛇" 可能无法匹配 "贪吃蛇"）
- 混合方案：明确的请求走快速通道，模糊的请求走 LLM

### 3.5 Memory — 记忆系统 (`core/memory.py`)

`MemoryStore` 封装了两类持久化数据：

| 数据 | 文件 | 格式 |
|------|------|------|
| 对话历史 | `memory/chat_history.json` | OpenAI messages 数组 |
| 用户画像 | `memory/user.json` | JSON 键值对 |

**核心方法**：

```python
memory.add_message("user", "你好")         # 追加对话
memory.get_history()                       # 获取完整历史
memory.get_user_profile()                  # 获取用户画像
memory.build_system_prompt("prompts/...")  # 渲染系统提示词
memory.initialize_system_message()         # 确保第一条消息是系统提示词
```

**设计意图**：接口与实现分离。当前后端是 JSON 文件，未来可以替换为 SQLite、Redis 等，只需实现相同的接口。

### 3.6 Tool 系统 (`tools/`)

工具是可供技能调用的**可复用功能模块**。设计上与 Skill 系统对称：

```python
class MyTool(BaseTool):
    name = "my_tool"

    def run(self, **kwargs) -> Any:
        # 工具逻辑
        return result
```

技能通过 `tools.get("file_tool")` 获取工具实例，然后调用 `.run()`。

| 内置工具 | 功能 |
|---------|------|
| `file_tool` | 写入文件到磁盘（自动创建父目录） |
| `browser_tool` | 在系统默认浏览器中打开 HTML 文件 |

---

## 4. 数据流：一次完整的请求

```
用户输入: "给我做一个俄罗斯方块"
    │
    ▼
main.py  →  Agent.start()  →  _run_loop()
    │
    ▼
Router.route("给我做一个俄罗斯方块", skill_registry)
    │
    ├─ Phase 1: GameGeneratorSkill.match_score() = 3/20 = 0.15
    │           (匹配到 "游戏"、"俄罗斯方块"、"小游戏")
    │           0.15 < 0.25 → 进入 Phase 2
    │
    ├─ Phase 2: LLM 路由
    │   Prompt: "可用技能: game_generator — 生成HTML5游戏 | chat — 通用对话"
    │   LLM 返回: "game_generator"
    │
    ▼
skill_registry.get("game_generator")  →  GameGeneratorSkill 实例
    │
    ▼
GameGeneratorSkill.execute(
    user_input  = "给我做一个俄罗斯方块",
    memory      = MemoryStore,
    tools       = ToolRegistry,
    config      = AgentConfig
)
    │
    ├─ 构建生成 Prompt
    ├─ 调用 LLM (DeepSeek API) 生成 HTML
    ├─ 清洗输出 (去除 ```html ``` 标记)
    ├─ tools.get("file_tool").run(path="output/game.html", content=html)
    ├─ tools.get("browser_tool").run(path="output/game.html")
    │
    ▼
SkillResult(
    skill_name = "game_generator",
    output     = "游戏生成成功！\n📁 保存位置：...",
    artifacts  = ["...output/game.html"]
)
    │
    ▼
Agent._display_result(result)
    │
    ▼
MemoryStore.save()  ← 对话历史持久化
    │
    ▼
下一个循环 → 等待用户输入
```

---

## 5. 添加新技能（Step-by-Step）

以添加一个 **天气查询技能** 为例：

### Step 1：创建文件

在 `skills/` 目录下新建 `weather.py`：

```python
from typing import List, Any, TYPE_CHECKING
from skills.base import BaseSkill, SkillResult

if TYPE_CHECKING:
    from core.memory import MemoryStore
    from tools.registry import ToolRegistry

class WeatherSkill(BaseSkill):

    @property
    def name(self) -> str:
        return "weather"

    @property
    def description(self) -> str:
        return "查询任意城市的实时天气和预报"

    @property
    def keywords(self) -> List[str]:
        return ["天气", "weather", "温度", "下雨", "刮风",
                "多少度", "冷不冷", "热不热", "天气预报"]

    def execute(
        self,
        user_input: str,
        memory: "MemoryStore",
        tools: "ToolRegistry",
        config: Any,
    ) -> SkillResult:
        # TODO: 接入天气 API
        # 可以使用 config.create_client() 获取 LLM 客户端
        return SkillResult(
            skill_name="weather",
            output=f"天气功能开发中... 你问了: {user_input}",
        )
```

### Step 2：重启 Agent

```bash
python main.py
```

启动日志会显示：

```
  [SkillRegistry] Registered skill: chat
  [SkillRegistry] Registered skill: game_generator
  [SkillRegistry] Registered skill: weather      ← 新技能已自动注册
```

### Step 3：使用

```
你：今天杭州天气怎么样

[Router] Keyword match → weather (score=0.25)

[weather] 天气功能开发中... 你问了: 今天杭州天气怎么样
```

**无需修改 `main.py`、`router.py`、`agent.py` 或任何配置文件。** 这就是框架的核心价值。

---

## 6. 添加新工具（Step-by-Step）

### Step 1：创建文件

在 `tools/` 目录下新建 `http_tool.py`：

```python
from tools.base import BaseTool

class HttpTool(BaseTool):
    """发送 HTTP 请求并返回响应"""

    @property
    def name(self) -> str:
        return "http_tool"

    def run(self, url: str = "", method: str = "GET", **kwargs) -> str:
        # 实现 HTTP 请求逻辑
        import requests
        resp = requests.request(method, url)
        return resp.text
```

### Step 2：在技能中使用

```python
def execute(self, user_input, memory, tools, config):
    http = tools.get("http_tool")
    data = http.run(url="https://api.example.com/data")
    ...
```

---

## 7. 配置详解 (`config.py`)

### AgentConfig 字段

| 字段 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| `api_key` | `DEEPSEEK_API_KEY` | `""` | LLM API 密钥 |
| `base_url` | `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `model` | `AGENT_MODEL` | `deepseek-v4-pro` | 模型名称 |
| `memory_dir` | — | `./memory` | 记忆存储目录 |
| `skills_dir` | — | `./skills` | 技能插件目录 |
| `tools_dir` | — | `./tools` | 工具目录 |
| `prompts_dir` | — | `./prompts` | 提示词模板目录 |
| `output_dir` | — | `./output` | 输出文件目录 |

### 设置 API Key

```bash
# Linux / macOS
export DEEPSEEK_API_KEY="sk-your-key-here"

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-key-here"

# Windows CMD
set DEEPSEEK_API_KEY=sk-your-key-here
```

### 切换模型

```bash
# 使用其他 DeepSeek 模型
export AGENT_MODEL="deepseek-chat"

# 使用 OpenAI
export DEEPSEEK_API_KEY="sk-openai-key"
export DEEPSEEK_BASE_URL="https://api.openai.com/v1"
export AGENT_MODEL="gpt-4o"
```

---

## 8. 扩展点

框架在以下位置提供了明确的扩展接口：

### 8.1 通过继承 Agent 扩展

```python
from core.agent import Agent

class WebAgent(Agent):
    """通过 WebSocket 接收输入，通过 HTTP 返回结果"""

    def _get_input(self) -> str:
        # 从 WebSocket 读取
        return self.websocket.recv()

    def _display_result(self, result) -> None:
        # 通过 HTTP Response 返回 JSON
        self.response.json({"output": result.output, ...})

    def _should_exit(self, user_input: str) -> bool:
        return user_input == "/stop"
```

### 8.2 通过自定义 Memory 后端扩展

```python
class SQLiteMemory(MemoryStore):
    def load(self): ...
    def save(self): ...
    def add_message(self, role, content): ...
```

### 8.3 通过自定义 Router 扩展

```python
class SemanticRouter(Router):
    """使用 Embedding 相似度进行路由"""
    def route(self, user_input, skill_registry, model) -> str:
        # 计算 embedding 相似度
        ...
```

---

## 9. 目录职责总结

| 目录 | 职责 | 修改频率 |
|------|------|---------|
| `core/` | 框架内核：调度、路由、记忆 | **低** — 框架稳定后不应频繁修改 |
| `skills/` | 技能插件：每个技能一个文件 | **高** — 最常新增的目录 |
| `tools/` | 可复用工具：供技能调用 | **中** — 有新需求时添加 |
| `prompts/` | 提示词模板：影响 LLM 行为 | **中** — 调整 Agent 人设时修改 |
| `memory/` | 运行时持久化数据 | **自动** — 由 MemoryStore 管理 |
| `output/` | 生成的输出文件 | **自动** — 由技能写入 |
| `config.py` | 全局配置 | **低** — 初始设置后基本不变 |
| `main.py` | 启动入口 | **极低** — 几乎不需要修改 |

---

## 10. 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| LLM 后端 | DeepSeek API（兼容 OpenAI SDK） |
| 数据格式 | JSON (memory/) + 纯文本 (prompts/) |
| 依赖 | `openai` Python SDK |
| 无额外依赖 | 不需要 LangChain、LlamaIndex 等框架 |

---

## 附录：内置技能说明

### ChatSkill (`chat`)

- **触发方式**：后备技能，无关键词匹配
- **功能**：通用对话，维护完整的对话上下文
- **特殊行为**：`match_score()` 永远返回 `0.0`，`keywords` 为空列表
- **用途**：确保任何输入都能得到回复

### GameGeneratorSkill (`game_generator`)

- **触发关键词**：游戏、贪吃蛇、俄罗斯方块、snake、tetris 等
- **功能**：根据自然语言描述生成完整的 HTML5 网页游戏
- **输出**：单文件 HTML → `output/game.html`，并自动打开浏览器
- **用途**：演示框架的完整技能开发模式（LLM调用 → 文件I/O → 浏览器操作）
