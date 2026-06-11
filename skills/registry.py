"""
Skill registry with auto-discovery.

Scans skills/*.py at startup and registers all BaseSkill subclasses.
No manual registration needed — just drop a .py file into skills/.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from skills.base import BaseSkill


class SkillRegistry:
    """Auto-discovering registry for skills.

    On initialization, scans the skills/ directory for .py files,
    imports each module, and registers every BaseSkill subclass found.

    Usage:
        registry = SkillRegistry("skills")
        skill = registry.get("game_generator")
        result = skill.execute(user_input, memory, tools, config)
    """

    def __init__(self, skills_dir: str = ""):
        self._skills: Dict[str, "BaseSkill"] = {}
        self._skills_dir = skills_dir or str(Path(__file__).parent)

        if Path(self._skills_dir).exists():
            self._discover()

    def _discover(self) -> None:
        """Scan skills/*.py and register all BaseSkill subclasses."""
        skills_path = Path(self._skills_dir)

        for filepath in sorted(skills_path.glob("*.py")):
            module_name = filepath.stem

            # Skip framework-internal modules
            if module_name.startswith("_") or module_name in ("base", "registry"):
                continue

            try:
                module = importlib.import_module(f"skills.{module_name}")
            except ImportError as e:
                print(f"  [SkillRegistry] Warning: could not import skills.{module_name}: {e}")
                continue

            found = False
            for _, obj in inspect.getmembers(module, inspect.isclass):
                # Need to import BaseSkill locally to avoid circular imports
                from skills.base import BaseSkill

                if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                    instance = obj()
                    self._skills[instance.name] = instance
                    print(f"  [SkillRegistry] Registered skill: {instance.name}")
                    found = True

            if not found:
                print(f"  [SkillRegistry] Warning: skills.{module_name} has no BaseSkill subclass")

    def get(self, name: str) -> Optional["BaseSkill"]:
        """Get a skill by name. Returns None if not found."""
        return self._skills.get(name)

    def list_skills(self) -> List["BaseSkill"]:
        """Return all registered skill instances."""
        return list(self._skills.values())

    def register(self, skill: "BaseSkill") -> None:
        """Manually register a skill instance."""
        self._skills[skill.name] = skill
        print(f"  [SkillRegistry] Manually registered skill: {skill.name}")

    def get_skill_names(self) -> List[str]:
        """Return list of registered skill names."""
        return list(self._skills.keys())
