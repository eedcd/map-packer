"""配置读取工具"""

import json

# 当前唯一支持的配置文件格式版本
SUPPORTED_VERSION = "0.0.1"


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
