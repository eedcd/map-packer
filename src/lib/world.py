"""世界优化工具

包含两类处理：

- 剔除未改动区块（prune）：参考 Minecraft 的区块存储格式，识别由世界噪声
  生成后从未被改动过的原始区块并删除其数据这类区块可依据世界种子重新
  生成，因此删除后既不破坏地形，又能显著减小存档体积
- 优化世界（optimize）：参考 Minecraft「优化世界」中的 eraseCache 行为，
  删除 Heightmaps、isLightOn 以及每个 section 的 BlockLight / SkyLight，
  让游戏首次进入存档时重新计算光照与高度图

区块字段名与实体存放位置随游戏版本变化（1.17 拆分实体、1.18 区块扁平化、
1.14 起才有光照缓存标记），具体行为由配置的 game_version 决定
"""

from __future__ import annotations

import gzip
import io
import zlib
from pathlib import Path

import nbtlib
from nbtlib import Compound

from lib.config import GameVersion

# region 文件按 4KiB 扇区对齐，前两个扇区为头部（位置表 + 时间戳表）
SECTOR_SIZE = 4096
HEADER_SIZE = SECTOR_SIZE * 2

# 压缩类型，与 region 文件格式一致
_COMPRESSION_GZIP = 1
_COMPRESSION_ZLIB = 2
_COMPRESSION_NONE = 3

# 需要擦除的缓存字段
_CACHE_KEYS = ("Heightmaps", "isLightOn")
_SECTION_LIGHT_KEYS = ("BlockLight", "SkyLight")

# 1.18 起实体与计划刻改为下划线字段，更早的版本用 Level 下的大驼峰字段
# 两套命名同时检查，避免配置的版本与实际存档不一致时误删区块
_CHUNK_CONTENT_KEYS = (
    "entities",
    "block_entities",
    "block_ticks",
    "fluid_ticks",
    "Entities",
    "TileEntities",
    "TileTicks",
    "ToBeTicked",
    "LiquidTicks",
    "LiquidsToBeTicked",
)

# 结构起点字段，1.18 前后分别为 structures.starts 与 Structures.Starts
_STRUCTURE_KEYS = (("structures", "starts"), ("Structures", "Starts"))

# 每个 region 最多容纳 32 × 32 个区块
_CHUNKS_PER_REGION = 32 * 32


def _decompress(data: bytes, compression: int) -> bytes | None:
    """按压缩类型解压区块数据，不支持的压缩返回 None"""
    if compression == _COMPRESSION_GZIP:
        return gzip.decompress(data)
    if compression == _COMPRESSION_ZLIB:
        return zlib.decompress(data)
    if compression == _COMPRESSION_NONE:
        return data
    return None


def _compress(data: bytes, compression: int) -> bytes | None:
    """按压缩类型压缩区块数据，与源文件保持一致"""
    if compression == _COMPRESSION_GZIP:
        # mtime 固定为 0，保证同一份数据每次压缩结果完全一致
        return gzip.compress(data, mtime=0)
    if compression == _COMPRESSION_ZLIB:
        return zlib.compress(data)
    if compression == _COMPRESSION_NONE:
        return data
    return None


def _strip_cache(chunk: Compound) -> bool:
    """删除区块及其 section 中的缓存字段，返回是否有改动"""
    # 1.18 起为扁平结构，更早版本的数据包在 Level 之下
    level = chunk["Level"] if "Level" in chunk else chunk
    changed = False

    for key in _CACHE_KEYS:
        if key in level:
            del level[key]
            changed = True

    sections = level.get("sections")
    if sections is None:
        sections = level.get("Sections")
    for section in sections or ():
        for key in _SECTION_LIGHT_KEYS:
            if key in section:
                del section[key]
                changed = True

    return changed


def _level_of(chunk: Compound) -> Compound:
    """返回承载区块字段的复合标签

    1.18 起为扁平结构，更早版本的数据包在 ``Level`` 之下
    """
    return chunk["Level"] if "Level" in chunk else chunk


def _parse_chunk(raw: bytes) -> tuple[nbtlib.File, int] | None:
    """解析区块原始字节，返回 (NBT 文件, 压缩类型)；无法处理时返回 None"""
    length = int.from_bytes(raw[:4], "big", signed=True)
    # 负数或零表示空区块 / 外置 .mcc 区块，保持原样
    if length <= 0:
        return None

    compression = raw[4]
    payload = _decompress(raw[5:5 + length - 1], compression)
    if payload is None:
        return None

    try:
        return nbtlib.File.parse(io.BytesIO(payload)), compression
    except Exception:
        return None


def _reencode_chunk(raw: bytes) -> bytes | None:
    """擦除单个区块缓存并重新编码；无改动或无法处理时返回 None"""
    parsed = _parse_chunk(raw)
    if parsed is None:
        return None

    chunk, compression = parsed
    if not _strip_cache(chunk):
        return None

    buffer = io.BytesIO()
    chunk.write(buffer)
    compressed = _compress(buffer.getvalue(), compression)
    if compressed is None:
        return None

    # 长度字段 = 压缩类型字节 + 压缩数据
    return (len(compressed) + 1).to_bytes(4, "big") + bytes((compression,)) + compressed


def _is_empty_list(tag) -> bool:
    """判断列表标签是否缺失或为空"""
    return tag is None or len(tag) == 0


def _has_post_processing(level: Compound) -> bool:
    """判断区块是否存在待处理的后处理标记"""
    offsets = level.get("PostProcessing")
    if offsets is None:
        return False
    return any(len(section) > 0 for section in offsets)


def _is_pristine(level: Compound) -> bool:
    """判断区块是否为「世界噪声生成后从未被改动」的原始区块

    参考 Minecraft 的区块存储内容（见 SerializableChunkData），全部满足以下
    条件才视为未改动，任一条不满足则保留：

    - ``InhabitedTime`` 为 0：没有任何玩家在区块附近停留过；
    - 没有方块实体、实体与计划刻（方块刻 / 流体刻）；
    - 没有任何待处理的后处理标记；
    - 没有任何结构起点

    1.18 起区块字段改为下划线命名，更早的版本字段名在 Level 之下，
    这里同时检查两套命名

    这类区块可安全删除，游戏会依据世界种子重新生成相同的地形
    """
    if int(level.get("InhabitedTime", 0)) != 0:
        return False

    for key in _CHUNK_CONTENT_KEYS:
        if not _is_empty_list(level.get(key)):
            return False

    if _has_post_processing(level):
        return False

    for container, starts_key in _STRUCTURE_KEYS:
        structures = level.get(container)
        if structures is not None and len(structures.get(starts_key) or {}) > 0:
            return False

    return True


def _is_pristine_chunk(raw: bytes) -> bool:
    """判断原始区块字节是否为可删除的未改动区块"""
    parsed = _parse_chunk(raw)
    if parsed is None:
        return False
    chunk, _compression = parsed
    return _is_pristine(_level_of(chunk))


def _entities_file(region: Path) -> Path | None:
    """返回 region 文件对应的 entities 区域文件

    1.17 起实体存放在维度目录下与 region 平级的 entities 目录
    """
    if region.parent.name != "region":
        return None
    return region.parent.parent / "entities" / region.name


def _chunk_has_entities(entities: bytes | None, index: int) -> bool:
    """判断 entities 区域文件中同一区块是否存有实体

    无法解析时按存有实体处理，避免误删
    """
    if not entities or len(entities) < HEADER_SIZE:
        return False

    entry = int.from_bytes(entities[index * 4:index * 4 + 4], "big")
    offset, count = entry >> 8, entry & 0xFF
    if offset < 2 or count == 0:
        return False

    raw = entities[offset * SECTOR_SIZE:offset * SECTOR_SIZE + count * SECTOR_SIZE]
    if len(raw) < 5:
        return False

    parsed = _parse_chunk(raw)
    if parsed is None:
        return True

    chunk, _compression = parsed
    return not _is_empty_list(chunk.get("Entities"))


def _rebuild_region(
    original_header: bytes, entries: list[tuple[int, bytes]]
) -> bytes | None:
    """按扇区重新排列区块数据并重建 region 文件

    Args:
        original_header: 原始 region 头部（位置表 + 时间戳表）
        entries: ``(区块索引, 区块字节)`` 列表，按原顺序排列

    Returns:
        重建后的字节；无法安全重建时返回 None
    """
    header = bytearray(HEADER_SIZE)
    payload = bytearray()
    sector = 2

    for index, blob in entries:
        sector_count = (len(blob) + SECTOR_SIZE - 1) // SECTOR_SIZE
        if sector_count > 255:
            # 仅删除数据时不会触发，保底放弃以避免破坏文件
            return None
        header[index * 4:index * 4 + 4] = (
            (sector << 8) | sector_count
        ).to_bytes(4, "big")
        # 仅保留仍然存在的区块的时间戳
        header[SECTOR_SIZE + index * 4:SECTOR_SIZE + index * 4 + 4] = (
            original_header[SECTOR_SIZE + index * 4:SECTOR_SIZE + index * 4 + 4]
        )
        payload += blob
        payload += b"\x00" * (sector_count * SECTOR_SIZE - len(blob))
        sector += sector_count

    return bytes(header) + bytes(payload)


def _build_pruned(
    data: bytes,
    version: GameVersion,
    entities_data: bytes | None = None,
) -> tuple[bytes, int]:
    """删除 region 文件中未改动的原始区块，返回 (处理后的字节, 删除区块数)

    1.17 起实体存放在独立的 entities 区域文件，同一区块内有实体时保留
    未删除任何区块时原样返回输入字节
    """
    if len(data) < HEADER_SIZE:
        return data, 0

    original_header = data[:HEADER_SIZE]
    entries: list[tuple[int, bytes]] = []
    removed = 0

    for index in range(_CHUNKS_PER_REGION):
        entry = int.from_bytes(original_header[index * 4:index * 4 + 4], "big")
        offset, count = entry >> 8, entry & 0xFF
        if offset < 2 or count == 0:
            continue

        raw = data[offset * SECTOR_SIZE:offset * SECTOR_SIZE + count * SECTOR_SIZE]
        if len(raw) < 5:
            continue

        if _is_pristine_chunk(raw):
            if version.split_entities and _chunk_has_entities(entities_data, index):
                entries.append((index, raw))
            else:
                removed += 1
        else:
            entries.append((index, raw))

    if removed == 0:
        return data, 0

    rebuilt = _rebuild_region(original_header, entries)
    if rebuilt is None:
        return data, 0
    return rebuilt, removed


def _build_optimized(data: bytes) -> tuple[bytes, int]:
    """擦除 region 文件中的区块缓存，返回 (优化后字节, 改动区块数)

    未发生改动时原样返回输入字节
    """
    if len(data) < HEADER_SIZE:
        return data, 0

    original_header = data[:HEADER_SIZE]
    entries: list[tuple[int, bytes]] = []
    changed = 0

    for index in range(_CHUNKS_PER_REGION):
        entry = int.from_bytes(original_header[index * 4:index * 4 + 4], "big")
        offset, count = entry >> 8, entry & 0xFF
        if offset < 2 or count == 0:
            continue

        raw = data[offset * SECTOR_SIZE:offset * SECTOR_SIZE + count * SECTOR_SIZE]
        if len(raw) < 5:
            continue

        body = _reencode_chunk(raw)
        if body is None:
            entries.append((index, raw))
        else:
            entries.append((index, body))
            changed += 1

    if changed == 0:
        return data, 0

    rebuilt = _rebuild_region(original_header, entries)
    if rebuilt is None:
        return data, 0
    return rebuilt, changed


def _optimize_region(path: Path) -> int:
    """擦除单个 region 文件的区块缓存，返回改动的区块数

    仅重新编码发生改动的区块，其余区块按原字节保留
    """
    data = path.read_bytes()
    optimized, changed = _build_optimized(data)
    if changed == 0:
        return 0
    path.write_bytes(optimized)
    return changed


def _prune_region(path: Path, version: GameVersion) -> int:
    """删除单个 region 文件中未改动的原始区块，返回删除的区块数"""
    data = path.read_bytes()

    entities_data: bytes | None = None
    if version.split_entities:
        entities_path = _entities_file(path)
        if entities_path is not None and entities_path.exists():
            try:
                entities_data = entities_path.read_bytes()
            except OSError:
                # 读不到实体数据时放弃处理，避免连同实体一起丢失
                return 0

    pruned, removed = _build_pruned(data, version, entities_data)
    if removed == 0:
        return 0
    path.write_bytes(pruned)
    return removed


def _transform_region(
    source: bytes,
    prune: bool,
    optimize: bool,
    version: GameVersion,
    entities_data: bytes | None = None,
) -> tuple[bytes, int, int]:
    """按 prune / optimize 顺序处理 region 字节

    1.17 起需要同时传入同一区块在 entities 区域文件中的数据

    Returns:
        (处理后的字节, 删除区块数, 擦除缓存区块数)
    """
    removed = 0
    changed = 0
    if prune:
        source, removed = _build_pruned(source, version, entities_data)
    if optimize:
        source, changed = _build_optimized(source)
    return source, removed, changed


def _read_entities(region: Path, version: GameVersion) -> bytes | None:
    """读取 region 文件对应的实体数据，旧版本或无文件时返回 None"""
    if not version.split_entities:
        return None
    path = _entities_file(region)
    if path is None or not path.exists():
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def region_matches(
    src: Path, dst: Path, prune: bool, optimize: bool, version: GameVersion
) -> bool:
    """判断 dst 是否等于 src 经 prune / optimize 处理后的结果

    prune 与 optimize 都会重写 region 文件，使目标文件不再与源逐字节一致
    同步时借此识别这类「已处理但内容未变」的文件，避免误判为改动而重复复制
    """
    try:
        source = src.read_bytes()
        target = dst.read_bytes()
    except OSError:
        return False

    transformed, removed, changed = _transform_region(
        source, prune, optimize, version, _read_entities(src, version)
    )
    return (removed > 0 or changed > 0) and transformed == target


def _terrain_regions(root: Path):
    """产出存档目录下的地形区域文件

    entities / poi 目录同样存放 .mca，但它们是实体与兴趣点数据，
    区块结构与地形不同，不能按地形区块处理
    """
    for path in sorted(root.rglob("*.mca")):
        if path.parent.name == "region":
            yield path


def prune_world(root: Path, version: GameVersion) -> tuple[int, int]:
    """删除 root 目录下所有 region 文件中未改动的原始区块

    Args:
        root: 待处理的存档目录（通常为同步后的目标目录）
        version: 游戏版本，决定实体是否存放在独立的 entities 区域文件

    Returns:
        (改动的 region 文件数, 删除的区块数)
    """
    files = 0
    chunks = 0
    for region in _terrain_regions(root):
        try:
            removed = _prune_region(region, version)
        except OSError:
            continue
        if removed:
            files += 1
            chunks += removed
    return files, chunks


def optimize_world(root: Path) -> tuple[int, int]:
    """擦除 root 目录下所有 region 文件的区块缓存

    Args:
        root: 待优化的存档目录（通常为同步后的目标目录）

    Returns:
        (改动的 region 文件数, 改动的区块数)
    """
    files = 0
    chunks = 0
    for region in _terrain_regions(root):
        try:
            changed = _optimize_region(region)
        except OSError:
            continue
        if changed:
            files += 1
            chunks += changed
    return files, chunks
