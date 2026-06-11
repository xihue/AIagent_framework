"""
Core Agent — orchestrates the entire agent lifecycle.

Wires together:
- Router → determines which skill handles input
- SkillRegistry → provides available skills
- ToolRegistry → provides reusable tools
- MemoryStore → manages conversation history + user profile

The Agent owns the main REPL loop. It is skill-agnostic:
add a new .py file to skills/ and it's automatically available.
"""

from __future__ import annotations

import sys
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from config import AgentConfig


class Agent:
    """The central agent orchestrator.

    Lifecycle:
        agent = Agent(config)
        agent.start()      # Bootstrap and enter REPL
        # ... user interacts ...
        # On exit or Ctrl+C:
        agent.shutdown()   # Save state, clean up

    Extension points (override in subclasses):
        _get_input()       → Custom input handling
        _display_result()  → Custom output formatting
        _should_exit()     → Custom exit conditions
        _on_startup()      → Pre-loop initialization
        _on_shutdown()     → Cleanup before exit
    """

    def __init__(self, config: "AgentConfig"):
        self.config = config

        # Lazy imports to avoid circular dependencies at module level
        from core.memory import MemoryStore
        from core.router import Router
        from skills.registry import SkillRegistry
        from tools.registry import ToolRegistry

        # Initialize subsystems
        print("Agent is booting up...")

        self.memory = MemoryStore(str(config.memory_dir))
        print(f"  Memory loaded ({len(self.memory.history)} messages)")

        self.tool_registry = ToolRegistry(str(config.tools_dir))

        self.skill_registry = SkillRegistry(str(config.skills_dir))

        self.router = Router()
        self.router._client = config.create_client()

        # Ensure the system message is fresh
        system_template = str(config.prompts_dir / "system.txt")
        self.memory.initialize_system_message(system_template)

        self._running = False

    # ── Public API ────────────────────────────────────────

    def start(self) -> None:
        """Bootstrap and enter the interactive REPL loop."""
        self._running = True
        self._on_startup()

        print(f"\n{'='*50}")
        print(f"  Personal AI Agent Framework v1.0")
        print(f"  Model: {self.config.model}")
        print(f"  Skills: {', '.join(self.skill_registry.get_skill_names())}")
        print(f"  Tools:  {', '.join(t.name for t in self.tool_registry.list_tools())}")
        print(f"{'='*50}")
        print("Type 'exit' or 'quit' to stop.\n")

        self._run_loop()

    def shutdown(self) -> None:
        """Save state and clean up resources."""
        if not self._running:
            return
        self._running = False
        self._on_shutdown()
        self.memory.save()
        print("Agent has shut down. Goodbye!")

    # ── Core Loop ─────────────────────────────────────────

    def _run_loop(self) -> None:
        """Main REPL (Read-Eval-Print Loop)."""
        while self._running:
            try:
                user_input = self._get_input()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue

            if self._should_exit(user_input):
                break

            # Route → Execute → Display
            skill_name = self.router.route(
                user_input,
                self.skill_registry,
                self.config.model,
            )

            skill = self.skill_registry.get(skill_name)
            if skill is None:
                print(f"\n  [Agent] Error: skill '{skill_name}' not found")
                continue

            print(f"\n[{skill_name}] ", end="")

            try:
                result = skill.execute(
                    user_input=user_input,
                    memory=self.memory,
                    tools=self.tool_registry,
                    config=self.config,
                )
                self._display_result(result)
            except Exception as e:
                print(f"\n  [Agent] Skill '{skill_name}' error: {e}")

    # ── Extension Points (override in subclasses) ──────────

    def _get_input(self) -> str:
        """Prompt for and return user input. Override for GUI/web hooks."""
        return input("\n你：").strip()

    def _display_result(self, result) -> None:
        """Display a skill execution result to the user.

        Override to support rich formatting, voice output, etc.
        """
        from skills.base import SkillResult

        if isinstance(result, SkillResult):
            print(result.output)
            if result.artifacts:
                print(f"\n  📄 Files: {', '.join(result.artifacts)}")
        else:
            print(result)

    def _should_exit(self, user_input: str) -> bool:
        """Check if the user wants to exit. Override for custom exit commands."""
        return user_input.lower() in ("exit", "quit", "退出")

    def _on_startup(self) -> None:
        """Hook called before the REPL loop starts."""
        pass

    def _on_shutdown(self) -> None:
        """Hook called during shutdown, before saving state."""
        pass
