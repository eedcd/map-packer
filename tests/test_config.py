"""Unit tests for config module"""

import pytest
from pathlib import Path
from lib.config import get_config, SUPPORTED_VERSION


class TestGetConfig:
    """测试配置文件读取"""

    def test_get_config_file_found(self, tmp_path):
        config_path = tmp_path / "test.json"
        config_path.write_text('{"version": "0.0.2", "name": "test"}')

        result = get_config(str(config_path))
        assert result == {"version": "0.0.2", "name": "test"}

    def test_get_config_file_missing(self, tmp_path):
        config_path = tmp_path / "nonexistent.json"

        result = get_config(str(config_path))
        assert result == {}

    def test_get_config_invalid_json(self, tmp_path):
        config_path = tmp_path / "invalid.json"
        config_path.write_text("not json")

        with pytest.raises(SystemExit):
            get_config(str(config_path))

    def test_get_config_default_path(self, tmp_path):
        # 测试默认路径 ./mmp.json
        config_path = tmp_path / "mmp.json"
        config_path.write_text('{"version": "0.0.2"}')

        import os
        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = get_config()
            assert result == {"version": "0.0.2"}
        finally:
            Path(old_cwd).chdir()


class TestSupportedVersion:
    """测试支持版本"""

    def test_version_string(self):
        assert isinstance(SUPPORTED_VERSION, str)
        assert SUPPORTED_VERSION == "0.0.2"
