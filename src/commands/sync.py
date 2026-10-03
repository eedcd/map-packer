"""地图同步命令

将 Minecraft 存档目录（由 .env 中的 SAVE_PATH 指定）同步到目标目录，
忽略规则通过 mmp.json 的 data.exclude 字段配置
"""

from __future__ import annotations

import fnmatch
import os
import shutil
import time
from pathlib import Path

import typer
from dotenv import find_dotenv, load_dotenv
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
from lib.world import optimize_world, prune_world, region_matches

DEFAULT_EXCLUDES = ()


def _load_ignore_patterns(patterns: list[str]) -> list[str]:
    """过滤空行与 # 注释行，返回有效的忽略规则

    会去掉规则开头的 "./"，因为匹配时使用的是不带该前缀的相对路径
    """
    cleaned: list[str] = []
    for raw in patterns:
        p = raw.strip()
        if not p or p.startswith("#"):
            continue
        negate = p.startswith("!")
        body = p[1:] if negate else p
        while body.startswith("./"):
            body = body[2:]
        cleaned.append(("!" if negate else "") + body)
    return cleaned


def _match_ignore(rel_path: str, is_dir: bool, patterns: list[str]) -> bool:
    """判断路径是否命中忽略规则（支持 ! 取反与目录规则）"""
    rel = rel_path.replace(os.sep, "/")
    rel_dir = rel + "/" if is_dir and not rel.endswith("/") else rel
    ignored = False

    for raw in patterns:
        negate = raw.startswith("!")
        pat = raw[1:] if negate else raw
        dir_only = pat.endswith("/")
        if dir_only:
            pat = pat.rstrip("/")

        candidates = [rel, rel_dir]
        name = rel.rsplit("/", 1)[-1]

        matched = False
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, pat):
                matched = True
                break
            if "/" not in pat and fnmatch.fnmatch(name, pat):
                matched = True
                break
            if pat.startswith("**/") and fnmatch.fnmatch(candidate, pat[3:]):
                matched = True
                break

        if dir_only and matched and not is_dir:
            matched = any(c.startswith(pat + "/") for c in candidates)

        if matched:
            ignored = not negate

    return ignored


def _iter_tree(root: Path, patterns: list[str]):
    """递归遍历目录，产出 (绝对路径, 相对路径) 并跳过被忽略的条目"""
    for dirpath, dir_names, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        dir_names[:] = [
            d
            for d in dir_names
            if not _match_ignore(
                os.path.join(rel_dir, d) if rel_dir else d,
                True,
                patterns,
            )
        ]

        for filename in filenames:
            rel = os.path.join(rel_dir, filename) if rel_dir else filename
            if _match_ignore(rel, False, patterns):
                continue
            yield Path(dirpath) / filename, rel


def _collect_source(save_path: Path, patterns: list[str]) -> dict[str, Path]:
    """扫描源目录，返回 {相对路径: 绝对路径} 映射"""
    files: dict[str, Path] = {}
    for full, rel in _iter_tree(save_path, patterns):
        files[rel.replace(os.sep, "/")] = full
    return files


def _same_file(a: Path, b: Path) -> bool:
    """比较两个文件是否一致（先比大小再比字节）"""
    try:
        if a.stat().st_size != b.stat().st_size:
            return False
        return a.read_bytes() == b.read_bytes()
    except OSError:
        return False


def _files_match(src: Path, dst: Path, optimize: bool, prune: bool) -> bzool:
    """判断源文件与目标文件是否一致

    启用 prune / optimize 时，已被剔除区块或擦除缓存的 region 文件与源文件
    内容语义相同，视为一致，避免处理后的目标文件每次都因内容差异被误判为改动
    """
    if _same_file(src, dst):
        return True
    if src.suffix == ".mca" and (optimize or prune):
        return region_matches(src, dst, prune=prune, optimize=optimize)
    return False


def _plan(
    source: dict[str, Path], target: Path, optimize: bool, prune: bool
):
    """计算同步计划，返回 (待复制列表, 待删除列表)"""
    to_copy: list[tuple[Path, Path]] = []
    to_delete: list[Path] = []

    for rel, src in source.items():
        dst = target / rel
        if dst.exists() and _files_match(src, dst, optimize, prune):
            continue
        to_copy.append((src, dst))

    if target.exists():
        for full, rel in _iter_tree(target, []):
            key = rel.replace(os.sep, "/")
            if key not in source:
                to_delete.append(full)

    return to_copy, to_delete


def _ensure_dir(path: Path) -> None:
    """确保目录存在，不存在则递归创建"""
    path.mkdir(parents=True, exist_ok=True)


def _copy_file(src: Path, dst: Path) -> None:
    """复制文件并保留元数据"""
    _ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def _remove_empty_dirs(root: Path) -> None:
    """自底向上删除目标目录中遗留的空目录"""
    if not root.exists():
        return
    for dirpath, _dir_names, _filenames in os.walk(root, topdown=False):
        current = Path(dirpath)
        if current == root:
            continue
        try:
            if not any(current.iterdir()):
                current.rmdir()
        except OSError:
            pass


def _dir_size(root: Path) -> int:
    """统计目录下所有文件的总字节数"""
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.stat().st_size
        except OSError:
            pass
    return total


def sync(
    config: str = typer.Option(
        "./mmp.json",
        "--config",
        "-c",
        help="Path to the mmp.json configuration file",
    ),
) -> None:
    """Sync the SAVE_PATH world save into the target directory.

    Rules:
    - files that are new or changed in the source are copied to the target;
    - files present only in the target are deleted;
    - the target directory, ignore rules and sync options come from the
      "data.sync" field in mmp.json;
    - mmp.json must declare version 0.0.2, the only supported format version.
    - when prune is enabled, chunks that were generated from world noise and never
      modified (no entities, block entities, ticks or block changes) are removed
      after syncing; the game regenerates them from the seed on first load.
    - when optimize is enabled, cached light and heightmap data is erased from
      the synced chunks so the game recomputes them on first load.
    - the size change and shrink percentage against the source save are reported
      after syncing.

    Args:
        config: Path to the mmp.json configuration file.

    Raises:
        typer.Exit: When SAVE_PATH is unset or is not a valid directory, or the
            mmp.json version is unsupported.
    """
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file)

    # 读取并校验存档目录
    save_path_raw = os.getenv("SAVE_PATH")
    if not save_path_raw:
        ui.error(
            "SAVE_PATH is not set",
            hint="add SAVE_PATH=<world save directory> to your .env",
        )
        raise typer.Exit(code=1)

    save_path = Path(save_path_raw).expanduser().resolve()
    if not save_path.is_dir():
        ui.error(
            f"SAVE_PATH is not a directory: [path]{escape(str(save_path))}[/path]",
            hint="point SAVE_PATH in .env at an existing world save",
        )
        raise typer.Exit(code=1)

    # 读取配置：忽略规则与同步选项位于 mmp.json 的 data.sync 字段
    config_data = get_config(config)
    version = config_data.get("version")
    if version != SUPPORTED_VERSION:
        ui.error(
            f"Unsupported mmp.json version: [path]{escape(str(version))}[/path]",
            hint=f"only version {SUPPORTED_VERSION} is supported",
        )
        raise typer.Exit(code=1)

    data = config_data.get("data") or {}
    sync_config = data.get("sync") or {}

    optimize = bool(sync_config.get("optimize", True))
    prune = bool(sync_config.get("prune", True))
    target_raw = sync_config.get("output_path", "./map")

    excludes = sync_config.get("exclude") or list(DEFAULT_EXCLUDES)
    patterns = _load_ignore_patterns(list(excludes))

    target = Path(target_raw).expanduser().resolve()
    _ensure_dir(target)

    # 打印同步概要
    ui.header("sync", "Pack a Minecraft world save into a clean directory")
    ui.panel(
        "Configuration",
        [
            ("Source", f"[path]{escape(str(save_path))}[/path]"),
            ("Target", f"[path]{escape(str(target))}[/path]"),
            ("Ignore", f"[num]{len(patterns)}[/num] [muted]pattern(s)[/muted]"),
            ("Prune", "[ok]enabled[/ok]" if prune else "[muted]disabled[/muted]"),
            ("Optimize", "[ok]enabled[/ok]" if optimize else "[muted]disabled[/muted]"),
        ],
    )
    ui.blank()

    started = time.perf_counter()

    # 扫描源目录并计算与目标目录的差异
    with ui.console.status("[brand]Scanning source…[/brand]", spinner="dots"):
        source = _collect_source(save_path, patterns)
    ui.phase("Scanning", f"[num]{len(source):,}[/num] [muted]files[/muted]")

    # 记录源存档总体积，用于展示同步与优化带来的体积变化
    source_size = 0
    for path in source.values():
        try:
            source_size += path.stat().st_size
        except OSError:
            pass

    with ui.console.status("[brand]Computing diff…[/brand]", spinner="dots"):
        to_copy, to_delete = _plan(source, target, optimize, prune)
    ui.phase(
        "Planning",
        f"[ok]+{len(to_copy):,}[/ok] [muted]add[/muted]   "
        f"[err]-{len(to_delete):,}[/err] [muted]remove[/muted]",
    )
    ui.blank()

    if not to_copy and not to_delete:
        ui.success("[bold]Already in sync[/bold] [muted]· nothing to do[/muted]")
    else:
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
            if to_copy:
                copy_task = progress.add_task(
                    ui.task_label("Copying"),
                    total=len(to_copy),
                )
                for src, dst in to_copy:
                    _copy_file(src, dst)
                    progress.advance(copy_task)

            if to_delete:
                delete_task = progress.add_task(
                    ui.task_label("Deleting"),
                    total=len(to_delete),
                )
                for file in to_delete:
                    try:
                        file.unlink()
                    except OSError:
                        pass
                    progress.advance(delete_task)

        _remove_empty_dirs(target)

        # 汇总耗时与变更数量
        elapsed = time.perf_counter() - started
        parts: list[str] = []
        if to_copy:
            parts.append(f"[ok]+{len(to_copy):,}[/ok] [muted]added[/muted]")
        if to_delete:
            parts.append(f"[err]-{len(to_delete):,}[/err] [muted]removed[/muted]")
        detail = f"  [muted]·[/muted]  {'  '.join(parts)}" if parts else ""
        ui.blank()
        ui.success(
            f"[bold]Sync complete[/bold] [muted]in {elapsed:.2f}s[/muted]{detail}"
        )

    # 剔除未改动区块：删除噪声生成后从未被改动的原始区块
    if prune:
        ui.blank()
        with ui.console.status("[brand]Pruning chunks…[/brand]", spinner="dots"):
            region_files, chunks = prune_world(target)
        if chunks:
            ui.phase(
                "Prune",
                f"[num]{chunks:,}[/num] [muted]chunk(s) in[/muted] "
                f"[num]{region_files:,}[/num] [muted]region file(s) removed[/muted]",
            )
        else:
            ui.phase("Prune", "[muted]nothing to prune[/muted]")

    # 优化世界：擦除区块缓存（eraseCache）
    if optimize:
        ui.blank()
        with ui.console.status("[brand]Optimizing world…[/brand]", spinner="dots"):
            region_files, chunks = optimize_world(target)
        if chunks:
            ui.phase(
                "Optimize",
                f"[num]{chunks:,}[/num] [muted]chunk(s) in[/muted] "
                f"[num]{region_files:,}[/num] [muted]region file(s) cleaned[/muted]",
            )
        else:
            ui.phase("Optimize", "[muted]already clean[/muted]")

    # 汇总体积变化：源存档总大小 → 同步并优化后的目录大小
    ui.blank()
    ui.phase("Size", ui.size_delta(source_size, _dir_size(target)))
