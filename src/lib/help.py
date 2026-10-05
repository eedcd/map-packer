"""帮助信息模块

从 src/helps/ 目录读取帮助文本文件，提供命令帮助查询、格式化与显示功能。
"""

from __future__ import annotations

import sys
from pathlib import Path

from rich.markup import escape
from rich.panel import Panel

from .ui import console, MARK


# 帮助文件路径
HELPS_DIR = Path(__file__).parent.parent / "helps"


def _load_help_file(name: str) -> str | None:
    """加载帮助文件内容

    Args:
        name: 文件名或命令名

    Returns:
        文件内容，如果未找到则返回 None
    """
    # 尝试不同的文件扩展名
    for ext in (".txt", ""):
        file_path = HELPS_DIR / f"{name}{ext}"
        if file_path.exists():
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception:
                pass
    return None


def get_command_help(command: str) -> tuple[str, str] | None:
    """获取命令的帮助信息（标题 + 内容）

    Args:
        command: 命令名称

    Returns:
        (标题，内容) 元组，未找到返回 None
    """
    content = _load_help_file(command)
    if content:
        # 第一行作为标题
        lines = content.strip().split("\n")
        if lines:
            title = lines[0]
            body = "\n".join(lines[1:])
            return (title, body)
    return None


def show_help(command: str | None = None) -> None:
    """显示帮助信息

    Args:
        command: 可选的命令名称。如果不提供，显示主帮助；如果提供，显示该命令的详细帮助
    """
    if command is None:
        _show_main_help()
    elif command == "version":
        _show_version_help()
    else:
        help_data = get_command_help(command)
        if help_data:
            title, content = help_data
            console.print()
            console.print(f"[brand]{MARK}[/brand]  [bold]mmp[/bold] [muted]·[/muted] [brand]help {command}[/brand]")
            console.print(f"   [muted]Help for the '{command}' command[/muted]")
            console.print()
            console.print(f"[bold]{title}[/bold]")
            console.print()
            console.print(content)
        else:
            console.print(f"[err]Unknown command:[/err] [muted]{command}[/muted]")
            console.print(f"[muted]→[/muted] Run [brand]mmp help</command> to see all commands")
            console.print()


def _show_main_help() -> None:
    """显示主帮助界面"""
    content = _load_help_file("help")
    if content:
        console.print()
        console.print(f"[brand]{MARK}[/brand]  [bold]mmp[/bold] [muted]·[/muted] [brand]help[/brand]")
        console.print(f"   [muted]Minecraft Map Packer CLI Tool</muted>")
        console.print()
        console.print(content)
    else:
        # 备用主帮助
        console.print()
        console.print(f"[brand]{MARK}[/brand]  [bold]mmp[/bold] [muted]·[/muted] [brand]help</brand>")
        console.print(f"   [muted]Minecraft Map Packer CLI Tool[/muted]")
        console.print()
        console.print("[brand]Commands:[/brand]")
        for cmd in ["init", "sync", "pack", "once", "help"]:
            console.print(f"  [value]{cmd:<10}[/value]  Help for {cmd}")
        console.print()
        console.print("[brand]Global Options:[/brand]")
        console.print("  --config, -c <path>  Path to the mmp.json configuration file")
        console.print("  --help, -h           Show this message and exit")
        console.print("  --version, -V        Show the version and exit")
        console.print()


def _show_version_help() -> None:
    """显示版本帮助"""
    try:
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as package_version

        try:
            current = package_version("map-packer")
        except PackageNotFoundError:
            current = "0.1.0"
    except Exception:
        current = "0.1.0"

    console.print()
    console.print(f"[brand]{MARK}[/brand]  [bold]mmp[/bold] [muted]·[/muted] [brand]version[/brand]")
    console.print(f"   [muted]Version information[/muted]")
    console.print()
    console.print(f"[value]Version:[/value]  [num]{current}[/num]")
    console.print()
    console.print("[value]Copyright[/value]  © 2024 map-packer contributors")
    console.print()

