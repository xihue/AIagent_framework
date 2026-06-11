"""
Memory store — manages conversation history and user profile persistence.

Default backend: JSON files (memory/chat_history.json, memory/user.json).
The interface allows swapping to SQLite, Redis, etc. in the future.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryStore:
    """Manages conversation history and user profile.

    Responsibilities:
    - Load/save chat history as OpenAI-compatible message list
    - Load/save user profile (name, role, goal, skills)
    - Build the system prompt from user profile + template
    - Provide a clean interface for skills to read/write memory

    Usage:
        memory = MemoryStore("memory")
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi! How can I help?")
        history = memory.get_history()
    """

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.history: List[Dict[str, str]] = []
        self.user_profile: Dict[str, Any] = {}

        # Ensure directory exists
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.load()

    # ── Persistence ─────────────────────────────────────────

    def load(self) -> None:
        """Load history and user profile from disk."""
        history_path = self.memory_dir / "chat_history.json"
        profile_path = self.memory_dir / "user.json"

        if history_path.exists():
            try:
                self.history = json.loads(
                    history_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, Exception):
                self.history = []

        if profile_path.exists():
            try:
                self.user_profile = json.loads(
                    profile_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, Exception):
                self.user_profile = {}

    def save(self) -> None:
        """Persist history and profile to disk."""
        history_path = self.memory_dir / "chat_history.json"

        history_path.write_text(
            json.dumps(self.history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Note: user profile is intentionally not auto-saved;
        # it's treated as read-only configuration. Use save_profile()
        # if you need to update it programmatically.

    def save_profile(self) -> None:
        """Persist user profile to disk."""
        profile_path = self.memory_dir / "user.json"
        profile_path.write_text(
            json.dumps(self.user_profile, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Conversation History ─────────────────────────────────

    def get_history(self) -> List[Dict[str, str]]:
        """Return a copy of the conversation history."""
        return list(self.history)

    def add_message(self, role: str, content: str) -> None:
        """Append a message to the conversation history and save.

        Args:
            role: 'user', 'assistant', or 'system'.
            content: The message content.
        """
        self.history.append({"role": role, "content": content})
        self.save()

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self.history = []
        self.save()

    # ── User Profile ─────────────────────────────────────────

    def get_user_profile(self) -> Dict[str, Any]:
        """Return a copy of the user profile."""
        return dict(self.user_profile)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific value from the user profile."""
        return self.user_profile.get(key, default)

    # ── System Prompt ────────────────────────────────────────

    def build_system_prompt(self, template_path: Optional[str] = None) -> str:
        """Render the system prompt template with user profile data.

        Args:
            template_path: Path to a .txt template with {placeholders}.
                           Defaults to prompts/system.txt.

        The template can use any keys from user.json as {placeholders}.
        Example template:
            "You are {name}'s personal AI assistant. Your goal: {goal}."

        Returns:
            The rendered system prompt string.
        """
        if template_path is None:
            template_path = str(
                self.memory_dir.parent / "prompts" / "system.txt"
            )

        template_file = Path(template_path)
        if not template_file.exists():
            # Fallback: minimal system prompt
            name = self.user_profile.get("name", "User")
            role = self.user_profile.get("role", "Assistant")
            return (
                f"You are {name}'s personal AI {role}. "
                f"Be helpful, concise, and proactive."
            )

        template = template_file.read_text(encoding="utf-8")

        # Preprocess profile data: convert lists to comma-joined strings
        format_data = {}
        for key, value in self.user_profile.items():
            if isinstance(value, list):
                format_data[key] = ", ".join(str(v) for v in value)
            else:
                format_data[key] = value

        # Ensure fallback defaults
        format_data.setdefault("name", "User")
        format_data.setdefault("role", "AI Assistant")
        format_data.setdefault("goal", "Be helpful")
        format_data.setdefault("skills", "General")

        try:
            return template.format(**format_data)
        except KeyError as e:
            print(f"  [MemoryStore] Warning: template key {e} not in user profile")
            return template.format(**format_data)

    # ── Lifecycle ────────────────────────────────────────────

    def initialize_system_message(self, template_path: Optional[str] = None) -> None:
        """Ensure the conversation starts with a system message.

        If the history is empty, inserts a dynamically-rendered system prompt
        as the first message. If a stale system message exists, replaces it.
        """
        system_prompt = self.build_system_prompt(template_path)

        if not self.history:
            self.history.append({"role": "system", "content": system_prompt})
            self.save()
        elif self.history[0].get("role") == "system":
            # Replace stale system message with fresh one
            self.history[0]["content"] = system_prompt
            self.save()
