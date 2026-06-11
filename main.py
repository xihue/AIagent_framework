"""
Personal AI Agent — Main Entry Point
=====================================

A modular, extensible AI Agent framework.

Usage:
    python main.py              # Interactive REPL mode
    python main.py --config     # Show current configuration

Before running:
    export DEEPSEEK_API_KEY="sk-your-key-here"

Add a new skill:
    1. Create a .py file in skills/
    2. Define a class inheriting from BaseSkill
    3. Restart — it's auto-discovered!
"""

import sys
from config import AgentConfig


def main():
    """Bootstrap the agent and enter the REPL loop."""
    print("=" * 50)
    print("  Personal AI Agent Framework v1.0")
    print("=" * 50)

    # Build configuration
    config = AgentConfig.from_env()

    if "--config" in sys.argv:
        print(config.summary())
        return

    # Validate API key
    if not config.api_key:
        print()
        print("⚠️  API key not configured.")
        print()
        print("  Set the environment variable:")
        print("    export DEEPSEEK_API_KEY=sk-your-key-here")
        print()
        print("  Or edit config.py to set a default.")
        sys.exit(1)

    # Ensure directories
    config.ensure_directories()

    # Bootstrap agent (lazy imports keep startup fast)
    from core.agent import Agent

    agent = Agent(config)

    try:
        agent.start()
    except KeyboardInterrupt:
        print("\n\nAgent interrupted. Shutting down...")
    finally:
        agent.shutdown()


if __name__ == "__main__":
    main()
