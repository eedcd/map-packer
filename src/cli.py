"""map-packer 命令行入口

集中注册各个子命令，提供 Minecraft 地图打包相关的命令行工具
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

import typer

from commands.init import init as init_command
from commands.pack import pack as pack_command
from commands.sync import sync as sync_command
from lib import ui


def _patch_typer_console() -> None:
    """让 typer 自带的帮助与错误输出也保留颜色

    typer 会自行创建 console，在 ConPTY 终端（Trae、VS Code）中它会重新把
    终端判定为「legacy Windows」，从而静默去掉 ``--help`` 的所有颜色
    复用我们强制 ANSI 的设置，让整个 CLI 的观感保持一致
    """
    try:
        from typer import rich_utils
    except ImportError:  # pragma: no cover - typer 始终带有 rich_utils
        return

    original = rich_utils._get_rich_console

    def _get_rich_console(stderr: bool = False):
        console = original(stderr=stderr)
        console.legacy_windows = False
        return console

    rich_utils._get_rich_console = _get_rich_console


_patch_typer_console()


def _version_callback(value: bool) -> None:
    """处理 --version：打印版本号并退出"""
    if not value:
        return
    try:
        current = package_version("map-packer")
    except PackageNotFoundError:
        current = "0.1.0"
    ui.console.print(f"[brand]mmp[/brand] [muted]v{current}[/muted]")
    raise typer.Exit()


# 全局 CLI 应用，no_args_is_help 让用户直接运行时可看到帮助信息
app = typer.Typer(
    name="mmp",
    help="A Minecraft Map Packer CLI Tool",
    epilog="Run [brand]mmp <command> --help[/brand] for details on a command.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# 注册子命令：mmp init
app.command(name="init", help="Initialize the current directory as an mmp repository")(
    init_command
)

# 注册子命令：mmp sync
app.command(name="sync", help="Sync a world save into the target directory")(sync_command)

# 注册子命令：mmp pack
app.command(name="pack", help="Pack the map directory into a compressed archive")(
    pack_command
)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Minecraft 地图打包命令行工具"""


if __name__ == "__main__":
    app()
