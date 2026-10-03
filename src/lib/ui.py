"""终端 UI 主题与排版辅助

集中定义 CLI 的配色、图标与常用排版块，让各命令拥有一致、清晰的视觉风格
设计参考 uv 与 docker：用品牌色突出关键信息，用语义色区分状态，
只有次要信息才使用弱化色
"""

from __future__ import annotations

import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

# 语义化主题，所有颜色都通过名称引用，保证调色板集中在一处
THEME = Theme(
    {
        "brand": "bold bright_cyan",
        "ok": "bold bright_green",
        "err": "bold bright_red",
        "key": "bold bright_blue",
        "value": "bold white",
        "path": "bright_cyan",
        "num": "bold bright_yellow",
        "muted": "dim",
    }
)

# IDE 终端（Trae、VS Code）与 ConPTY 会话经常错误地设置 TERM=dumb，导致
# rich 以及 typer 自带的帮助输出去掉所有颜色该值仅在 stdout 为 TTY 时才
# 有意义，因此覆盖它不会把转义码泄漏到管道输出中
if os.environ.get("TERM", "").lower() in ("dumb", "unknown"):
    os.environ["TERM"] = "xterm-256color"


def _detect_color_system() -> str | None:
    """选择颜色系统，同时尊重 NO_COLOR 与非 TTY 输出"""
    if os.environ.get("NO_COLOR"):
        return None
    if os.environ.get("FORCE_COLOR"):
        return "truecolor"
    if not sys.stdout.isatty():
        return None
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return "truecolor"
    if "256color" in os.environ.get("TERM", "").lower():
        return "256"
    return "truecolor" if sys.platform == "win32" else "standard"


# highlight=False 关闭 rich 的自动高亮，保证输出颜色完全可控
# legacy_windows=False 强制输出 ANSI：rich 的 legacy 检测在现代 ConPTY 终端
# 中会失效，从而静默地丢掉全部颜色
console = Console(
    theme=THEME,
    highlight=False,
    color_system=_detect_color_system(),
    legacy_windows=False,
)

# 统一图标，保证各命令视觉一致
MARK = "◆"
OK = "✓"

# 阶段名右对齐到该宽度，使不同阶段的信息落在同一列
LABEL_WIDTH = 10


def header(command: str, tagline: str) -> None:
    """打印命令标题：品牌名 + 子命令 + 一行说明"""
    console.print()
    console.print(
        f"[brand]{MARK}[/brand]  [bold]mmp[/bold] "
        f"[muted]·[/muted] [brand]{command}[/brand]"
    )
    console.print(f"   [muted]{tagline}[/muted]")
    console.print()


def panel(title: str, pairs: list[tuple[str, str]]) -> None:
    """打印带边框的「键 / 值」面板"""
    grid = Table.grid(padding=(0, 2))
    grid.add_column(justify="right", style="key", no_wrap=True)
    grid.add_column(style="value")
    for label, value in pairs:
        grid.add_row(label, value)
    console.print(
        Panel(
            grid,
            title=f"[brand]{title}[/brand]",
            title_align="left",
            border_style="brand",
            padding=(1, 2),
            expand=False,
        )
    )


def phase(label: str, detail: str) -> None:
    """打印已完成的阶段行：右对齐的阶段名 + 结果说明"""
    console.print(f"  [brand]{label:>{LABEL_WIDTH}}[/brand]  {detail}")


def task_label(label: str) -> str:
    """把阶段名格式化为进度条描述，保持与 phase() 相同的列宽"""
    return f"[brand]{label:>{LABEL_WIDTH}}[/brand]"


def success(message: str) -> None:
    """打印成功提示"""
    console.print(f"[ok]{OK}[/ok]  {message}")


def error(message: str, hint: str | None = None) -> None:
    """打印错误提示，可选附带一行修复建议"""
    console.print(f"[err]error:[/err] {message}")
    if hint:
        console.print(f"       [muted]→ {hint}[/muted]")


def blank() -> None:
    """打印一个空行"""
    console.print()


def format_size(size: int) -> str:
    """把字节数格式化为易读的大小字符串"""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def size_delta(before: int, after: int) -> str:
    """格式化体积变化：原始大小 → 产物大小 · 减少/增加量与百分比"""
    if before <= 0:
        return "[muted]n/a[/muted]"

    delta = before - after
    percent = abs(delta) / before * 100
    base = (
        f"[muted]{format_size(before)}[/muted] [muted]→[/muted] "
        f"[value]{format_size(after)}[/value] [muted]·[/muted] "
    )
    if delta > 0:
        return f"{base}[ok]↓ {format_size(delta)}[/ok] [muted]({percent:.1f}% smaller)[/muted]"
    if delta < 0:
        return f"{base}[err]↑ {format_size(-delta)}[/err] [muted]({percent:.1f}% larger)[/muted]"
    return f"{base}[muted]unchanged[/muted]"
