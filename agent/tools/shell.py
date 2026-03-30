"""
Shell tool - allows the agent to execute shell commands.
"""

import subprocess

from .base import Tool


class ShellTool(Tool):
    """Tool for executing shell commands."""

    name = "shell"
    description = "Execute a shell command and return its output. Use for running programs, listing files, etc."

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "One single shell command to execute, of type string.",
                }
            },
            "required": ["command"],
        }

    def execute(self, dir: str, command: str) -> str:
        """Execute the shell command and return its output."""
        if dir is None:
            dir = "."
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout for safety
                cwd=dir,  
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += result.stderr
            if result.returncode != 0:
                output += f"\n(exit code: {result.returncode})"
            return output.strip() if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {e}"
