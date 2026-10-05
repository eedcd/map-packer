"""一次性打包命令

一个简单的无状态打包命令，直接指定输入和输出即可使用。
适用于快速打包而不依赖配置文件。
"""

from __future__ import annotations

import tarfile
import time
import zipfile
from pathlib import Path

import typer
from rich.markup import escape
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from lib import ui
from lib.datapack import minify_datapacks

# 默认配置
DEFAULT_FORMAT = "zip"
DEFAULT_COMPRESSION_LEVEL = 6
DEFAULT_MINIFY_DATAPACK = True

# 支持的打包格式及其输出扩展名
FORMATS: dict[str, str] = {
    "zip": ".zip",
    "tar": ".tar",
    "tar.gz": ".tar.gz",
    "tar.bz2": ".tar.bz2",
    "tar.xz": ".tar.xz",
}

# 常见别名统一归一化为标准格式名
FORMAT_ALIASES: dict[str, str] = {
    "tgz": "tar.gz",
    "tbz": "tar.bz2",
    "tbz2": "tar.bz2",
    "txz": "tar.xz",
}


def _normalize_format(raw: str) -> str:
    """把用户填写的格式归一化为标准格式名，未知格式原样返回"""
    fmt = raw.strip().lower()
    return FORMAT_ALIASES.get(fmt, fmt)


def _level_range(fmt: str) -> tuple[int, int] | None:
    """返回指定格式支持的压缩等级范围，tar 不支持压缩时返回 None"""
    if fmt == "tar":
        return None
    if fmt == "tar.bz2":
        return (1, 9)
    return (0, 9)


def _collect_files(root: Path) -> list[tuple[Path, str]]:
    """收集目录下所有文件，返回 (绝对路径, 归档内相对路径) 列表"""
    files: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append((path, path.relative_to(root).as_posix()))
    return files


def _write_zip(target: Path, files: list[tuple[Path, str]], level: int, advance) -> None:
    """把文件写入 zip 归档，level 为 0 时改用仅存储模式"""
    if level == 0:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as zf:
            for full, rel in files:
                zf.write(full, arcname=rel)
                advance()
        return

    with zipfile.ZipFile(
        target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=level
    ) as zf:
        for full, rel in files:
            zf.write(full, arcname=rel)
            advance()


def _write_tar(target: Path, fmt: str, files: list[tuple[Path, str]], level: int, advance) -> None:
    """把文件写入 tar 归档，按格式选择对应的压缩器与参数"""
    mode = {
        "tar": "w",
        "tar.gz": "w:gz",
        "tar.bz2": "w:bz2",
        "tar.xz": "w:xz",
    }[fmt]

    kwargs: dict[str, int] = {}
    if fmt in ("tar.gz", "tar.bz2"):
        kwargs["compresslevel"] = level
    elif fmt == "tar.xz":
        kwargs["preset"] = level

    with tarfile.open(target, mode, **kwargs) as tf:
        for full, rel in files:
            tf.add(full, arcname=rel)
            advance()


def once(
    input_path: str = typer.Argument(
        None,
        help="Input directory containing the map files",
    ),
    output: str = typer.Option(
        None,
        "-o",
        "--output",
        help="Output path for the archive",
    ),
    format: str = typer.Option(
        DEFAULT_FORMAT,
        "-f",
        "--format",
        help="Archive format (zip, tar, tar.gz, tar.bz2, tar.xz)",
    ),
    level: int = typer.Option(
        DEFAULT_COMPRESSION_LEVEL,
        "-l",
        "--level",
        help="Compression level (0-9, 0 for no compression)",
    ),
    minify: bool = typer.Option(
        DEFAULT_MINIFY_DATAPACK,
        "-m",
        "--minify",
        help="Minify datapacks (remove comments and whitespace)",
    ),
) -> None:
    """Quickly pack a map directory into a compressed archive.

    A simple stateless command that requires just the input directory and
    output path. No configuration files needed.

    Args:
        input_path: Directory containing the map files to pack.
        output: Output path for the archive.
        format: Archive format.
        level: Compression level.
        minify: Whether to minify datapacks.

    Raises:
        typer.Exit: When input is missing, output is missing, or parameters are invalid.
    """
    # 校验输入
    if input_path is None:
        ui.error("[err]Missing input path[/err]")
        ui.error("       [muted]→ Provide the input directory as the first argument: mmp once <input-path>[/muted]")
        raise typer.Exit(code=1)

    if output is None:
        ui.error("[err]Missing output path[/err]")
        ui.error("       [muted]→ Use -o or --output to specify: mmp once <input> -o <output>[/muted]")
        raise typer.Exit(code=1)

    source = Path(input_path).expanduser().resolve()
    target = Path(output).expanduser().resolve()

    fmt = _normalize_format(format)

    # 校验源目录
    if not source.is_dir():
        ui.error(
            f"Input directory not found: [path]{escape(str(source))}[/path]",
            hint="check the provided path and try again",
        )
        raise typer.Exit(code=1)

    # 校验打包格式
    if fmt not in FORMATS:
        supported = ", ".join(FORMATS)
        ui.error(
            f"Unsupported pack format: [path]{escape(fmt)}[/path]",
            hint=f"supported formats: {supported}",
        )
        raise typer.Exit(code=1)

    # 校验压缩等级
    bounds = _level_range(fmt)
    if bounds is not None and not bounds[0] <= level <= bounds[1]:
        ui.error(
            f"Invalid compression_level [num]{level}[/num] for format [path]{escape(fmt)}[/path]",
            hint=f"expected an integer between {bounds[0]} and {bounds[1]}",
        )
        raise typer.Exit(code=1)

    ui.header("once", "Pack the map directory into a compressed archive quickly")
    ui.panel(
        "Configuration",
        [
            ("Input", f"[path]{escape(str(source))}[/path]"),
            ("Output", f"[path]{escape(str(target))}[/path]"),
            ("Format", f"[value]{escape(fmt)}[/value]"),
            ("Level", f"[num]{level}[/num]" if bounds else "[muted]n/a[/muted]"),
            ("Minify", "[ok]enabled[/ok]" if minify else "[muted]disabled[/muted]"),
        ],
    )
    ui.blank()

    with ui.console.status("[brand]Scanning files…[/brand]", spinner="dots"):
        files = _collect_files(source)
    ui.phase("Scanning", f"[num]{len(files):,}[/num] [muted]files[/muted]")

    if not files:
        ui.error(
            f"No files found in [path]{escape(str(source))}[/path]",
            hint="check the provided path and try again",
        )
        raise typer.Exit(code=1)

    # 记录精简前的源目录总体积
    source_size = sum(path.stat().st_size for path, _rel in files)

    # 精简数据包
    if minify:
        ui.blank()
        with ui.console.status("[brand]Minifying datapacks…[/brand]", spinner="dots"):
            datapack_files, datapack_saved = minify_datapacks(source)
        if datapack_files:
            ui.phase(
                "Minify",
                f"[num]{datapack_files:,}[/num] [muted]file(s) · saved[/muted] "
                f"[num]{ui.format_size(datapack_saved)}[/num]",
            )
        else:
            ui.phase("Minify", "[muted]nothing to minify[/muted]")

    # 确保输出目录存在
    target.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()

    columns: list[ProgressColumn] = [
        SpinnerColumn(style="brand"),
        TextColumn("{task.description}"),
        BarColumn(
            bar_width=None,
            complete_style="brand",
            finished_style="ok",
            pulse_style="brand",
        ),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    ]

    with Progress(*columns, console=ui.console) as progress:
        task = progress.add_task(ui.task_label("Packing"), total=len(files))

        def advance() -> None:
            progress.advance(task)

        if fmt == "zip":
            _write_zip(target, files, level, advance)
        else:
            _write_tar(target, fmt, files, level, advance)

    elapsed = time.perf_counter() - started
    size = target.stat().st_size

    ui.blank()
    ui.success(
        f"[bold]Pack complete[/bold] [muted]in {elapsed:.2f}s[/muted]  "
        f"[muted]·[/muted]  [num]{len(files):,}[/num] [muted]files →[/muted] "
        f"[path]{escape(str(target))}[/path] [muted]({ui.format_size(size)})[/muted]"
    )
    ui.phase("Size", ui.size_delta(source_size, size))

