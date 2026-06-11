"""
Base skill abstraction — the core extension point of the framework.

Every skill inherits from BaseSkill. The SkillRegistry auto-discovers
all BaseSkill subclasses in the skills/ directory at startup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.memory import MemoryStore
    from tools.registry import ToolRegistry


@dataclass
class SkillResult:
    """The result returned by a skill after execution.

    Attributes:
        skill_name: Name of the skill that produced this result.
        output: Human-readable output text to display to the user.
        artifacts: Optional list of generated file paths.
        metadata: Optional dict of arbitrary metadata.
    """

    skill_name: str
    output: str
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """Abstract base class for all skills.

    To create a new skill:
    1. Create a .py file in skills/
    2. Define a class inheriting from BaseSkill
    3. Implement: name, description, keywords, execute()
    4. Optionally override match_score() for custom routing priority
    5. Restart the agent — the SkillRegistry auto-discovers it

    Example:
        class WeatherSkill(BaseSkill):
            name = "weather"
            description = "Get weather forecasts for any city"
            keywords = ["天气", "weather", "温度", "下雨"]

            def execute(self, user_input, memory, tools, config):
                # ... fetch weather ...
                return SkillResult(skill_name="weather", output=forecast)
    """

    # ── Subclasses MUST override these ──────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique skill identifier used for routing (e.g., 'game_generator')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description shown in router prompts.

        Should answer: "What does this skill do?"
        """
        ...

    @property
    @abstractmethod
    def keywords(self) -> List[str]:
        """Keywords that trigger this skill during keyword-based routing.

        Use lowercase. The router checks if any keyword appears in the
        user's input. More specific keywords give better routing accuracy.

        Return an empty list if this skill should never match on keywords
        (e.g., the ChatSkill fallback).
        """
        ...

    @abstractmethod
    def execute(
        self,
        user_input: str,
        memory: "MemoryStore",
        tools: "ToolRegistry",
        config: Any,
    ) -> SkillResult:
        """Execute the skill with the given user input.

        Args:
            user_input: The raw user input text.
            memory: MemoryStore for reading/writing conversation history.
            tools: ToolRegistry for accessing reusable tools.
            config: AgentConfig with API keys, paths, model settings.

        Returns:
            SkillResult with output text and optional artifacts/metadata.
        """
        ...

    # ── Subclasses MAY override these ────────────────────────

    def match_score(self, user_input: str) -> float:
        """Calculate a keyword match score for the given input.

        Default: fraction of keywords that appear in the input.
        Override for custom matching logic (regex, semantic, etc.).

        Returns:
            A score from 0.0 (no match) to 1.0 (perfect match).
        """
        if not self.keywords:
            return 0.0

        text_lower = user_input.lower()
        matches = sum(1 for kw in self.keywords if kw in text_lower)
        return matches / max(len(self.keywords), 1)
