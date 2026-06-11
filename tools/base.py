"""
Base tool abstraction for the Agent framework.

Every tool inherits from BaseTool and is auto-discovered by ToolRegistry.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all tools.

    To create a new tool:
    1. Create a .py file in tools/
    2. Define a class inheriting from BaseTool
    3. Implement name (property) and run() (method)
    4. The ToolRegistry will auto-discover it at startup
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier (e.g., 'file_tool', 'browser_tool')."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description shown in tool listings."""
        return self.__doc__ or ""

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the tool with given parameters.

        Returns the result of the tool execution.
        """
        ...
