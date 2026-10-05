"""Test configuration and fixtures"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Automatically set up test environment"""
    # 将临时目录设置为工作目录
    monkeypatch.chdir(tmp_path)
    # 确保 sys.path 包含 src 目录
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    return tmp_path


@pytest.fixture
def sample_config(tmp_path):
    """创建一个示例 mmp.json 配置文件"""
    config = {
        "version": "0.0.2",
        "name": "test-map",
        "data": {
            "sync": {
                "save_path": "/tmp/testworld",
                "optimize": True,
                "prune": True,
                "output_path": "./map",
                "exclude": ["session.lock"],
            },
            "pack": {
                "input_path": "./map",
                "output_path": "./dist",
                "name": "{name} {date}-{hash}",
                "format": "zip",
                "compression_level": 6,
                "minify_datapack": True,
            },
        },
    }
    config_path = tmp_path / "mmp.json"
    config_path.write_text(config.__repr__())
    return config_path


@pytest.fixture
def temp_map_dir(tmp_path):
    """创建一个包含示例文件的地图目录"""
    map_dir = tmp_path / "map"
    map_dir.mkdir()
    (map_dir / "level.dat").write_text("fake data")
    (map_dir / "region").mkdir()
    (map_dir / "region" / "d-0.0.mca").write_text("fake region file")
    return map_dir


@pytest.fixture
def temp_save_dir(tmp_path):
    """创建一个示例世界存档目录"""
    save_dir = tmp_path / "save"
    save_dir.mkdir()
    (save_dir / "level.dat").write_text("world data")
    (save_dir / "session.lock").write_text("lock file")
    return save_dir


@pytest.fixture
def mock_console(monkeypatch):
    """创建一个 Mock 的 Rich console"""
    mock_console = MagicMock()
    monkeypatch.setattr("lib.ui.console", mock_console)
    return mock_console
