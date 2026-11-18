"""配置读取工具"""

import json
import re
from dataclasses import dataclass

# 默认游戏版本，决定按哪一版的存档结构处理
DEFAULT_GAME_VERSION = "26.3"

# 版本号格式：主版本.次版本[.修订号]，如 26.3、1.21.11
_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")


@dataclass(frozen=True)
class GameVersion:
    """Minecraft 游戏版本

    旧命名（1.21.11）与新命名（26.3）都按数值比较，新版本号更大，
    因此可以直接与旧版本阈值比较
    """

    major: int
    minor: int
    patch: int = 0

    def at_least(self, major: int, minor: int, patch: int = 0) -> bool:
        """判断版本是否不低于给定版本"""
        return (self.major, self.minor, self.patch) >= (major, minor, patch)

    @property
    def split_entities(self) -> bool:
        """1.17 起实体从区块中拆出，存放在独立的 entities 区域文件"""
        return self.at_least(1, 17)

    @property
    def cached_light(self) -> bool:
        """1.14 起区块用 isLightOn 与 Heightmaps 标记缓存，可擦除后由游戏重算"""
        return self.at_least(1, 14)

    def __str__(self) -> str:
        if self.patch:
            return f"{self.major}.{self.minor}.{self.patch}"
        return f"{self.major}.{self.minor}"


def parse_game_version(raw: object = None) -> GameVersion:
    """解析 game_version 配置，未填写时使用默认版本

    Raises:
        ValueError: 版本号格式不合法时
    """
    text = str(raw or DEFAULT_GAME_VERSION).strip()
    match = _VERSION_PATTERN.match(text)
    if match is None:
        raise ValueError(f"invalid game version: {text}")
    major, minor, patch = (int(part) if part else 0 for part in match.groups())
    return GameVersion(major, minor, patch)


def get_config(path: str = "./mmp.json") -> dict:
    """读取 JSON 格式的配置文件

    配置文件不存在时返回空字典，由调用方决定默认值

    Args:
        path: 配置文件路径，默认为当前目录下的 mmp.json

    Returns:
        解析后的配置字典；文件缺失时返回空字典
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
