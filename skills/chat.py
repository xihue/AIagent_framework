"""
Chat skill — general-purpose conversation using the LLM.

This is the default fallback skill. It handles any input that doesn't
match a more specific skill. It maintains conversation context via MemoryStore.
"""

from __future__ import annotations

from typing import Any, List, TYPE_CHECKING

from skills.base import BaseSkill, SkillResult

if TYPE_CHECKING:
    from core.memory import MemoryStore
    from tools.registry import ToolRegistry


class ChatSkill(BaseSkill):
    """General conversational skill — the default fallback.

    This skill has no keywords, so it never wins during keyword-based
    routing. It only activates when no other skill matches, or when
    explicitly requested by the LLM router.
    """

    @property
    def name(self) -> str:
        return "chat"

    @property
    def description(self) -> str:
        return "通用对话与问答 — 处理日常对话、知识问答、建议咨询等"

    @property
    def keywords(self) -> List[str]:
        # Empty: chat is the fallback, never triggered by keywords
        return []

    def match_score(self, user_input: str) -> float:
        # Never match on keywords — let other skills win
        return 0.0

    def execute(
        self,
        user_input: str,
        memory: "MemoryStore",
        tools: "ToolRegistry",
        config: Any,
    ) -> SkillResult:
        """Handle a conversational turn.

        Sends the full conversation history + user input to the LLM,
        appends the assistant's reply to memory, and returns it.
        """
        # Append user message
        memory.add_message("user", user_input)

        # Build the message list for the API call
        messages = memory.get_history()

        # Call LLM
        client = config.create_client()

        try:
            response = client.chat.completions.create(
                model=config.model,
                messages=messages,
            )
            assistant_reply = response.choices[0].message.content
        except Exception as e:
            assistant_reply = f"[对话出错: {e}]"

        # Save assistant reply
        memory.add_message("assistant", assistant_reply)

        return SkillResult(
            skill_name="chat",
            output=assistant_reply,
        )
