"""
Tool registry with auto-discovery.

Scans tools/*.py at initialization and registers all BaseTool subclasses.
Skills can then access tools via ToolRegistry.get(name).
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type

from tools.base import BaseTool


class ToolRegistry:
    """Auto-discovering registry for tools.

    On initialization, scans the tools/ directory for .py files,
    imports each module, and registers every BaseTool subclass found.
    """

    def __init__(self, tools_dir: str = ""):
        self._tools: Dict[str, BaseTool] = {}
        self._tools_dir = tools_dir or str(Path(__file__).parent)

        if Path(self._tools_dir).exists():
            self._discover()

    def _discover(self) -> None:
        """Scan tools/*.py and register all BaseTool subclasses."""
        tools_path = Path(self._tools_dir)

        for filepath in tools_path.glob("*.py"):
            module_name = filepath.stem

            # Skip framework-internal modules
            if module_name.startswith("_") or module_name in ("base", "registry"):
                continue

            try:
                module = importlib.import_module(f"tools.{module_name}")
            except ImportError as e:
                print(f"  [ToolRegistry] Warning: could not import tools.{module_name}: {e}")
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseTool) and obj is not BaseTool:
                    instance = obj()
                    self._tools[instance.name] = instance
                    print(f"  [ToolRegistry] Registered tool: {instance.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name. Returns None if not found."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """Return all registered tool instances."""
        return list(self._tools.values())

    def register(self, tool: BaseTool) -> None:
        """Manually register a tool instance."""
        self._tools[tool.name] = tool
        print(f"  [ToolRegistry] Manually registered tool: {tool.name}")
