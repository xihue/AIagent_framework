"""
File tool — writes content to disk with automatic directory creation.
"""

import os

from tools.base import BaseTool


class FileTool(BaseTool):
    """Write string content to a file, creating parent directories as needed."""

    @property
    def name(self) -> str:
        return "file_tool"

    def run(self, path: str = "", content: str = "", **kwargs) -> str:
        """Write content to the given file path.

        Args:
            path: Target file path (relative or absolute).
            content: String content to write.

        Returns:
            The absolute path of the written file.
        """
        abs_path = os.path.abspath(path)

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        return abs_path


# Backward-compatible function wrapper
def write_file(path: str, content: str) -> str:
    """Legacy wrapper — prefer FileTool.run() instead."""
    return FileTool().run(path=path, content=content)
