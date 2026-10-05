"""帮助命令

提供命令行的帮助信息，包括主帮助和各个子命令的详细帮助
"""

from __future__ import annotations

import typer

from lib import ui
from lib.help import show_help


def help(
    command: str | None = typer.Argument(
        None,
        help="Optional command name to show help for a specific command",
    ),
    config: str = typer.Option(
        "./mmp.json",
        "--config",
        "-c",
        help="Path to the mmp.json configuration file",
    ),
) -> None:
    """Show help information for commands.

    Run this command without arguments to see a list of all available commands.
    Provide a command name to see detailed help for that specific command.

    Args:
        command: The command to display help for. If omitted, shows main help.
        config: Path to the mmp.json configuration file (for commands that read config).

    Raises:
        typer.Exit: When an unknown command is provided.
    """
    ui.header("help", "Show help information for commands")
    show_help(command)

