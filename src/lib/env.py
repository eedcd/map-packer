"""环境变量读取工具"""

from os import PathLike, getenv

from dotenv import load_dotenv


class Env:
    """封装 .env 文件的加载与变量读取"""

    def __init__(self, dotenv_path: str | PathLike[str] | None = None) -> None:
        """加载 .env 文件

        Args:
            dotenv_path: 自定义 .env 路径，为空时按默认规则查找
        """
        load_dotenv(dotenv_path=dotenv_path)

    def __getitem__(self, name: str) -> str | None:
        """按名称读取环境变量，未设置时返回 None"""
        return getenv(name)
