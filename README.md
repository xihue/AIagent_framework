# Personal AI Agent Framework

一个**轻量级、模块化、可扩展**的 AI Agent 框架模板。核心理念：**技能即插件** —— 新增技能只需在 `skills/` 下创建一个 `.py` 文件，无需修改任何现有代码。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install openai
```

### 2. 配置 API Key

```bash
# Linux / macOS
export DEEPSEEK_API_KEY="sk-your-key-here"

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-key-here"
```

默认使用 DeepSeek API。如需切换到 OpenAI：

```bash
export DEEPSEEK_BASE_URL="https://api.openai.com/v1"
export AGENT_MODEL="gpt-4o"
```

### 3. 运行

```bash
cd "personal agentV1"
python main.py
```

```
Agent is booting up...
  Memory loaded (0 messages)
  [ToolRegistry] Registered tool: browser_tool
  [ToolRegistry] Registered tool: file_tool
  [SkillRegistry] Registered skill: chat
  [SkillRegistry] Registered skill: game_generator

==================================================
  Personal AI Agent Framework v1.0
  Model: deepseek-v4-pro
  Skills: chat, game_generator
  Tools:  browser_tool, file_tool
==================================================
Type 'exit' or 'quit' to stop.

你：你好
[chat] 你好！有什么我可以帮助你的？

你：给我做一个贪吃蛇游戏
[Router] Keyword match → game_generator (score=0.27)
[game_generator] 游戏生成成功！...
```

## 🧩 添加新技能

在 `skills/` 下创建 `weather.py`：

```python
from skills.base import BaseSkill, SkillResult

class WeatherSkill(BaseSkill):
    name = "weather"
    description = "查询任意城市的实时天气"
    keywords = ["天气", "weather", "温度", "多少度"]

    def execute(self, user_input, memory, tools, config):
        return SkillResult(
            skill_name="weather",
            output=f"天气查询结果：晴天 25°C",
        )
```

重启 Agent，技能自动注册。**就这么简单。**

## 📂 项目结构

```
├── main.py              # 入口
├── config.py            # 配置
├── core/                # 框架内核（agent, router, memory）
├── skills/              # 技能插件（chat, game_generator, ...）
├── tools/               # 可复用工具（file_tool, browser_tool）
├── prompts/             # 提示词模板
├── memory/              # 对话历史 & 用户画像
└── output/              # 生成的文件
```

## 📖 详细文档

见 [ARCHITECTURE.md](./ARCHITECTURE.md)

## 🔧 配置参考

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `DEEPSEEK_API_KEY` | LLM API 密钥 | — |
| `DEEPSEEK_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `AGENT_MODEL` | 模型名称 | `deepseek-v4-pro` |

## 📄 许可

MIT — 自由使用、修改、分发。
