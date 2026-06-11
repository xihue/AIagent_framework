"""
Game generator skill — generates HTML5 browser games from text descriptions.

This is an EXAMPLE skill. It demonstrates:
- How to use the ToolRegistry for file I/O and browser opening
- How to access the LLM client via config
- How to parse/clean LLM output
- How to return a SkillResult with artifacts

Feel free to copy this file as a template for your own skills.
"""

from __future__ import annotations

from typing import Any, List, TYPE_CHECKING

from skills.base import BaseSkill, SkillResult

if TYPE_CHECKING:
    from config import AgentConfig
    from core.memory import MemoryStore
    from tools.registry import ToolRegistry


class GameGeneratorSkill(BaseSkill):
    """Generate complete HTML5 browser games from natural language descriptions.

    Supports requests like:
    - "做一个贪吃蛇游戏"
    - "生成一个飞机大战"
    - "make me a tetris game"
    - "帮我做一个塔防游戏"
    """

    @property
    def name(self) -> str:
        return "game_generator"

    @property
    def description(self) -> str:
        return "根据文字描述生成完整的HTML5网页游戏（贪吃蛇、飞机大战、俄罗斯方块等）"

    @property
    def keywords(self) -> List[str]:
        return [
            # Chinese keywords
            "游戏", "制作游戏", "生成游戏", "小游戏",
            "贪吃蛇", "飞机大战", "俄罗斯方块", "塔防",
            "跑酷", "射击", "打砖块", "拼图",
            "扫雷", "2048", "五子棋", "象棋",
            "HTML游戏", "网页游戏", "browser game",
            # English keywords
            "game", "snake", "tetris", "pacman",
            "shooter", "tower defense", "platformer",
        ]

    def execute(
        self,
        user_input: str,
        memory: "MemoryStore",
        tools: "ToolRegistry",
        config: "AgentConfig",
    ) -> SkillResult:
        """Generate an HTML5 game from the user's description.

        Steps:
        1. Build a detailed game-generation prompt
        2. Call the LLM to generate HTML
        3. Clean the response (strip markdown artifacts)
        4. Write to output/game.html via FileTool
        5. Open in browser via BrowserTool
        """
        prompt = self._build_prompt(user_input)
        client = config.create_client()

        # ── Generate HTML ────────────────────────────────
        try:
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": prompt}],
            )
            html = response.choices[0].message.content
        except Exception as e:
            return SkillResult(
                skill_name=self.name,
                output=f"游戏生成失败（API调用错误）：{e}",
            )

        # ── Clean markdown artifacts ─────────────────────
        html = html.replace("```html", "").replace("```", "").strip()

        # ── Write to file ────────────────────────────────
        file_tool = tools.get("file_tool")
        browser_tool = tools.get("browser_tool")

        if file_tool is None:
            return SkillResult(
                skill_name=self.name,
                output="错误：缺少 file_tool，无法保存游戏文件",
            )

        path = file_tool.run(
            path=str(config.output_dir / "game.html"),
            content=html,
        )

        # ── Open in browser ──────────────────────────────
        browser_msg = ""
        if browser_tool is not None:
            try:
                browser_tool.run(path=path)
                browser_msg = "\n浏览器已自动打开"
            except Exception:
                browser_msg = "\n（浏览器打开失败，请手动打开）"

        return SkillResult(
            skill_name=self.name,
            output=(
                f"游戏生成成功！\n\n"
                f"📁 保存位置：{path}\n"
                f"{browser_msg}\n\n"
                f"提示：你可以继续让我修改这个游戏，比如：\n"
                f"「把背景改成黑色」「加快游戏速度」「增加分数显示」"
            ),
            artifacts=[path],
            metadata={"html_length": len(html)},
        )

    # ── Private Helpers ──────────────────────────────────

    def _build_prompt(self, user_request: str) -> str:
        """Build the game generation prompt."""
        return f"""根据用户需求生成完整HTML页面。

用户需求：
{user_request}

要求：

1. 返回完整HTML代码
2. 包含CSS样式
3. 页面美观
4. 单文件实现
5. 不要解释
6. 不要Markdown代码块
7. 直接返回HTML源码"""
