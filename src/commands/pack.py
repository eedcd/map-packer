"""地图打包命令

将同步后的地图目录打包为压缩文件，打包格式、压缩等级与输出位置
通过 mmp.json 的 data.pack 字段配置
"""

from __future__ import annotations

import hashlib
import tarfile
import time
import zipfile
from datetime import datetime
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
from lib.config import SUPPORTED_VERSION, get_config
from lib.datapack import minify_datapacks

# 各配置项的默认值，字段与 init 写入的 data.pack 保持一致
DEFAULT_INPUT = "./map"
DEFAULT_OUTPUT = "./dist"
DEFAULT_MAP_NAME = "map"
DEFAULT_NAME = "{name} {date}-{hash}"
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


def _expand_name(template: str, map_name: str) -> str:
    """把 pack.name 模板展开为最终归档名

    支持的占位符：
    - {name}      地图名称，来自配置顶层的 name 字段
    - {date}      当前日期，格式 YYYYMMDD
    - {time}      当前时间，格式 HHMMSS
    - {datetime}  当前日期时间，格式 YYYYMMDDHHMMSS
    - {timestamp} 当前 Unix 时间戳（秒）
    - {hash}      时间戳 SHA-256 摘要的前 6 位十六进制字符
    """
    now = time.time()
    moment = datetime.fromtimestamp(now)
    fields = {
        "name": map_name,
        "date": moment.strftime("%Y%m%d"),
        "time": moment.strftime("%H%M%S"),
        "datetime": moment.strftime("%Y%m%d%H%M%S"),
        "timestamp": str(int(now)),
        "hash": hashlib.sha256(str(int(now)).encode("utf-8")).hexdigest()[:6],
    }

    try:
        expanded = template.format_map(fields)
    except KeyError as exc:
        unknown = str(exc).strip("'")
        ui.error(
            f"Unknown placeholder [path]{{{escape(unknown)}}}[/path] "
            f"in [path]data.pack.name[/path]",
            hint="available placeholders: " + ", ".join(f"{{{key}}}" for key in fields),
        )
        raise typer.Exit(code=1)
    except ValueError as exc:
        ui.error(
            f"Invalid [path]data.pack.name[/path] template: {escape(str(exc))}"
        )
        raise typer.Exit(code=1)

    expanded = expanded.strip()
    if not expanded:
        ui.error(
            "[path]data.pack.name[/path] template produced an empty name",
            hint="set a non-empty name or use placeholders such as {name}",
        )
        raise typer.Exit(code=1)
    return expanded


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


def pack(
    config: str = typer.Option(
        "./mmp.json",
        "--config",
        "-c",
        help="Path to the mmp.json configuration file",
    ),
) -> None:
    """Pack the target directory into a compressed archive.

    Rules:
    - the source directory, output directory, archive name, format and
      compression level come from the "data.pack" field in mmp.json;
    - "data.pack.name" is a template: {name} is the map name from the
      top-level "name" field, while {date}, {time}, {datetime}, {timestamp}
      and {hash} (first 6 hex chars of the timestamp SHA-256) expand at pack
      time;
    - when "data.pack.minify_datapack" is enabled, datapack text files have their
      comments (lines starting with #) and blank lines removed, and every JSON
      file is rewritten without indentation or spaces before packing;
    - the packed size change and shrink percentage are reported when packing;
    - supported formats are zip, tar, tar.gz, tar.bz2 and tar.xz;
    - mmp.json must declare version 0.0.2, the only supported format version.

    Args:
        config: Path to the mmp.json configuration file.

    Raises:
        typer.Exit: When the source directory is missing, the format is
            unsupported, or the mmp.json version is unsupported.
    """
    # 读取配置：打包选项位于 mmp.json 的 data.pack 字段
    config_data = get_config(config)
    version = config_data.get("version")
    if version != SUPPORTED_VERSION:
        ui.error(
            f"Unsupported mmp.json version: [path]{escape(str(version))}[/path]",
            hint=f"only version {SUPPORTED_VERSION} is supported",
        )
        raise typer.Exit(code=1)

    data = config_data.get("data") or {}
    pack_config = data.get("pack") or {}

    source = (
        Path(pack_config.get("input_path", DEFAULT_INPUT)).expanduser().resolve()
    )
    output_dir = (
        Path(pack_config.get("output_path", DEFAULT_OUTPUT)).expanduser().resolve()
    )
    name = _expand_name(
        str(pack_config.get("name", DEFAULT_NAME)),
        str(config_data.get("name", DEFAULT_MAP_NAME)),
    )
    fmt = _normalize_format(str(pack_config.get("format", DEFAULT_FORMAT)))
    try:
        level = int(pack_config.get("compression_level", DEFAULT_COMPRESSION_LEVEL))
    except (TypeError, ValueError):
        ui.error(
            "Invalid [path]data.pack.compression_level[/path] in mmp.json",
            hint="expected an integer",
        )
        raise typer.Exit(code=1)
    minify = bool(pack_config.get("minify_datapack", DEFAULT_MINIFY_DATAPACK))

    # 校验源目录
    if not source.is_dir():
        ui.error(
            f"Input directory not found: [path]{escape(str(source))}[/path]",
            hint="run mmp sync first or point data.pack.input_path at a map directory",
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

    target = output_dir / f"{name}{FORMATS[fmt]}"

    ui.header("pack", "Pack the map directory into a compressed archive")
    ui.panel(
        "Configuration",
        [
            ("Source", f"[path]{escape(str(source))}[/path]"),
            ("Output", f"[path]{escape(str(target))}[/path]"),
            ("Name", f"[value]{escape(name)}[/value]"),
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
            hint="run mmp sync first to populate the map directory",
        )
        raise typer.Exit(code=1)

    # 记录精简前的源目录总体积，用于展示打包带来的体积变化
    source_size = sum(path.stat().st_size for path, _rel in files)

    # 精简数据包：去除注释与空行、把 JSON 压缩为无缩进无空格格式
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

    output_dir.mkdir(parents=True, exist_ok=True)
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
