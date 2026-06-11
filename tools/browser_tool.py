"""
Browser tool — opens files in the system's default web browser.
"""

import webbrowser
import os

from tools.base import BaseTool


class BrowserTool(BaseTool):
    """Open a local HTML file in the default web browser."""

    @property
    def name(self) -> str:
        return "browser_tool"

    def run(self, path: str = "", **kwargs) -> str:
        """Open the given file path in the browser.

        Args:
            path: Absolute or relative path to an HTML file.

        Returns:
            The absolute path that was opened.
        """
        abs_path = os.path.abspath(path)
        webbrowser.open(f"file://{abs_path}")
        return abs_path


# Backward-compatible function wrapper
def open_game(path: str) -> str:
    """Legacy wrapper — prefer BrowserTool.run() instead."""
    return BrowserTool().run(path=path)
