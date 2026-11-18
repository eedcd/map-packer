"""数据包精简工具

删除数据包目录下文本文件的注释行（以 # 开头）与空行，并把所有 JSON
文件重新编码为无缩进、无空格的紧凑格式，以减小数据包体积

仅在内存中生成精简后的内容，不修改源目录中的任何文件；精简结果由打包
命令写入归档，因此 dist 中的压缩包是精简后的，源地图保持原样

仅处理已知的文本类型，避免误伤纹理解析（.png）与结构文件（.nbt）等二进制内容
"""

from __future__ import annotations

import json
from pathlib import Path

# 需要处理的文本文件后缀
_TEXT_SUFFIXES = {".json", ".mcmeta", ".mcfunction", ".txt"}
# 需要重新编码为紧凑格式的 JSON 文件后缀
_JSON_SUFFIXES = {".json", ".mcmeta"}


def _is_comment_or_blank(line: str) -> bool:
    """判断一行是否为注释行（以 # 开头）或空行"""
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _strip_text(raw: str) -> str:
    """删除文本中的注释行与空行"""
    lines = [line for line in raw.splitlines() if not _is_comment_or_blank(line)]
    return "\n".join(lines)


def _compact_json(raw: str) -> str | None:
    """把 JSON 文本重新编码为无缩进无空格的紧凑格式；解析失败返回 None"""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _minify_file(path: Path) -> bytes | None:
    """精简单个数据包文件，返回精简后的内容；无需改动返回 None"""
    suffix = path.suffix.lower()
    if suffix not in _TEXT_SUFFIXES:
        return None

    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    # JSON 优先尝试紧凑编码，格式非法时退化为仅去除注释与空行
    compacted = _compact_json(raw) if suffix in _JSON_SUFFIXES else None
    new = compacted if compacted is not None else _strip_text(raw)
    if new == raw:
        return None
    return new.encode("utf-8")


def minify_datapacks(root: Path) -> tuple[dict[Path, bytes], int, int]:
    """精简 root/datapacks 目录下的所有数据包文件

    内容只在内存中生成，源文件保持不变

    Args:
        root: 地图目录（数据包位于其下的 datapacks 子目录）

    Returns:
        (以文件绝对路径为键的精简内容, 改动的文件数, 节省的字节数)
    """
    datapacks = root / "datapacks"
    overrides: dict[Path, bytes] = {}
    if not datapacks.is_dir():
        return overrides, 0, 0

    files = 0
    saved = 0
    for path in sorted(datapacks.rglob("*")):
        if not path.is_file():
            continue
        data = _minify_file(path)
        if data is None:
            continue
        overrides[path] = data
        files += 1
        try:
            saved += max(path.stat().st_size - len(data), 0)
        except OSError:
            continue
    return overrides, files, saved
