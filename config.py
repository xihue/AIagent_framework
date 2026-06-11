"""
Central configuration for the AI Agent Framework.

All sensitive values (API keys) should be set via environment variables,
not hardcoded here. See ARCHITECTURE.md for details.

Quick start:
    export DEEPSEEK_API_KEY="sk-your-key-here"
    python main.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ── Defaults (override via environment variables) ──────────

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-pro"


@dataclass
class AgentConfig:
    """Agent framework configuration.

    Every field can be set via environment variable or passed directly.
    Paths default to their conventional locations relative to this file.

    Attributes:
        api_key: LLM API key (env: DEEPSEEK_API_KEY)
        base_url: LLM API base URL (env: DEEPSEEK_BASE_URL)
        model: LLM model name (env: AGENT_MODEL)
        project_root: Root directory of the project
        memory_dir: Conversation history and user profile
        skills_dir: Pluggable skill modules
        tools_dir: Reusable tool modules
        prompts_dir: System prompt templates
        output_dir: Generated file output
    """

    # ── LLM Settings ───────────────────────────────────

    api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    model: str = field(default_factory=lambda: os.getenv("AGENT_MODEL", DEFAULT_MODEL))

    # ── Directory Paths ────────────────────────────────

    project_root: Path = field(default_factory=lambda: Path(__file__).parent)

    memory_dir: Path = field(default=None)
    skills_dir: Path = field(default=None)
    tools_dir: Path = field(default=None)
    prompts_dir: Path = field(default=None)
    output_dir: Path = field(default=None)

    def __post_init__(self):
        """Set default paths relative to project_root."""
        if self.memory_dir is None:
            self.memory_dir = self.project_root / "memory"
        if self.skills_dir is None:
            self.skills_dir = self.project_root / "skills"
        if self.tools_dir is None:
            self.tools_dir = self.project_root / "tools"
        if self.prompts_dir is None:
            self.prompts_dir = self.project_root / "prompts"
        if self.output_dir is None:
            self.output_dir = self.project_root / "output"

    # ── Factory Methods ────────────────────────────────

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create config entirely from environment variables."""
        return cls()

    # ── Utility Methods ────────────────────────────────

    def create_client(self):
        """Create an OpenAI-compatible client from this config.

        Uses lazy import so the openai package is only required
        when actually making API calls.
        """
        from openai import OpenAI

        if not self.api_key:
            raise ValueError(
                "API key not set. Please set the DEEPSEEK_API_KEY environment variable.\n"
                "Example: export DEEPSEEK_API_KEY=sk-your-key-here"
            )

        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def ensure_directories(self) -> None:
        """Create all configured directories if they don't exist."""
        for dir_path in [
            self.memory_dir,
            self.skills_dir,
            self.tools_dir,
            self.prompts_dir,
            self.output_dir,
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def summary(self) -> str:
        """Return a human-readable configuration summary."""
        return (
            f"Config:\n"
            f"  API Base: {self.base_url}\n"
            f"  Model:    {self.model}\n"
            f"  Memory:   {self.memory_dir}\n"
            f"  Skills:   {self.skills_dir}\n"
            f"  Tools:    {self.tools_dir}\n"
            f"  Prompts:  {self.prompts_dir}\n"
            f"  Output:   {self.output_dir}"
        )
