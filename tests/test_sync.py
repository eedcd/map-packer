"""Unit tests for sync command"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from commands.sync import (
    _load_ignore_patterns,
    _match_ignore,
    _collect_source,
    _same_file,
    _files_match,
    _plan,
    sync,
)


class TestLoadIgnorePatterns:
    """测试忽略规则加载"""

    def test_load_ignore_patterns_empty(self):
        patterns = _load_ignore_patterns([])
        assert patterns == []

    def test_load_ignore_patterns_with_comments(self):
        patterns = _load_ignore_patterns(["# comment", "  ", "ignore.txt"])
        assert patterns == ["ignore.txt"]

    def test_load_ignore_patterns_negate(self):
        patterns = _load_ignore_patterns(["!important.txt"])
        assert patterns == ["!important.txt"]

    def test_load_ignore_patterns_remove_dot_slash(self):
        patterns = _load_ignore_patterns(["./temp/", "data/"])
        assert patterns == ["temp/", "data/"]


class TestMatchIgnore:
    """测试忽略规则匹配"""

    def test_match_ignore_replace_lock(self):
        is_dir = False
        patterns = ["session.lock"]
        assert _match_ignore("session.lock", is_dir, patterns) is True

    def test_match_ignore_ignore_dir(self):
        is_dir = True
        patterns = ["node_modules/"]
        assert _match_ignore("node_modules/", is_dir, patterns) is True

    def test_match_ignore_negate(self):
        is_dir = False
        patterns = ["!important.txt"]
        assert _match_ignore("important.txt", is_dir, patterns) is False

    def test_match_ignore_no_match(self):
        is_dir = False
        patterns = ["*.log"]
        assert _match_ignore("test.txt", is_dir, patterns) is False


class TestCollectSource:
    """测试源文件收集"""

    def test_collect_source_empty(self, tmp_path):
        patterns = []
        result = _collect_source(tmp_path, patterns)
        assert result == {}

    def test_collect_source_with_files(self, tmp_path):
        # 创建文件结构
        (tmp_path / "file1.txt").write_text("test1")
        (tmp_path / "file2.txt").write_text("test2")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("test3")

        patterns = []
        result = _collect_source(tmp_path, patterns)

        assert len(result) == 3
        assert (tmp_path / "file1.txt").resolve() in result.values()
        assert (tmp_path / "file2.txt").resolve() in result.values()
        assert (subdir / "file3.txt").resolve() in result.values()


class TestSameFile:
    """测试文件比较"""

    def test_same_file_identical(self, tmp_path):
        file1 = tmp_path / "a.txt"
        file2 = tmp_path / "b.txt"
        file1.write_text("same content")
        file2.write_text("same content")

        assert _same_file(file1, file2) is True

    def test_same_file_different_size(self, tmp_path):
        file1 = tmp_path / "a.txt"
        file2 = tmp_path / "b.txt"
        file1.write_text("content")
        file2.write_text("different content")

        assert _same_file(file1, file2) is False

    def test_same_file_missing(self, tmp_path):
        file1 = tmp_path / "a.txt"
        file2 = tmp_path / "missing.txt"
        file1.write_text("content")

        assert _same_file(file1, file2) is False


class TestFilesMatch:
    """测试文件匹配（考虑优化）"""

    @patch("commands.sync.region_matches")
    def test_files_match_same_file(self, mock_region, tmp_path):
        file1 = tmp_path / "a.mca"
        file2 = tmp_path / "b.mca"
        file1.write_text("same data")
        file2.write_text("same data")

        assert _files_match(file1, file2, optimize=True, prune=True) is True
        mock_region.assert_not_called()

    @patch("commands.sync.region_matches")
    def test_files_match_different(self, mock_region, tmp_path):
        file1 = tmp_path / "a.mca"
        file2 = tmp_path / "b.mca"
        file1.write_text("data1")
        file2.write_text("data2")

        assert _files_match(file1, file2, optimize=True, prune=True) is False
        mock_region.assert_not_called()


class TestPlan:
    """测试同步计划"""

    def test_plan_no_changes(self, tmp_path):
        source = {}
        target = tmp_path / "target"
        target.mkdir()

        to_copy, to_delete = _plan(source, target, optimize=True, prune=True)
        assert to_copy == []
        assert to_delete == []

    def test_plan_add_files(self, tmp_path):
        source = {"file1.txt": tmp_path / "file1.txt"}
        target = tmp_path / "target"
        target.mkdir()

        to_copy, to_delete = _plan(source, target, optimize=True, prune=True)
        assert len(to_copy) == 1
        assert to_delete == []

    def test_plan_delete_extra(self, tmp_path):
        source = {}
        target = tmp_path / "target"
        target.mkdir()
        (target / "extra.txt").write_text("extra")

        to_copy, to_delete = _plan(source, target, optimize=True, prune=True)
        assert to_copy == []
        assert (target / "extra.txt") in to_delete


class TestSyncCommand:
    """测试同步命令"""

    @patch("commands.sync.ui")
    @patch("commands.sync.get_config")
    @patch("commands.sync.Path")
    def test_sync_missing_save_path(self, mock_path, mock_get_config, mock_ui):
        """测试缺少 save_path 配置"""
        mock_get_config.return_value = {"version": "0.0.2"}
        Path = mock_path()
        Path.exists.return_value = False

        with pytest.raises(SystemExit) as exc:
            sync()
        assert exc.value.code == 1
        mock_ui.error.assert_called()

    @patch("commands.sync.ui")
    @patch("commands.sync.get_config")
    @patch("commands.sync.Path.resolve")
    def test_sync_invalid_save_path(self, mock_resolve, mock_get_config, mock_ui):
        """测试无效的存档路径"""
        mock_get_config.return_value = {"version": "0.0.2", "data": {"sync": {"save_path": "/nonexistent"}}}
        Path = mock_resolve()
        Path.is_dir.return_value = False

        with pytest.raises(SystemExit) as exc:
            sync()
        assert exc.value.code == 1
        mock_ui.error.assert_called()

    @patch("commands.sync.ui")
    @patch("commands.sync.get_config")
    @patch("commands.sync._collect_source")
    @patch("commands.sync.Path.exists")
    @patch("commands.sync.Path.resolve")
    @patch("commands.sync.Path.mkdir")
    def test_sync_successful(self, mock_mkdir, mock_resolve, mock_exists, mock_collect,
                             mock_get_config, mock_ui, tmp_path):
        """测试成功同步"""
        mock_get_config.return_value = {
            "version": "0.0.2",
            "data": {
                "sync": {
                    "save_path": str(tmp_path),
                    "optimize": True,
                    "prune": True,
                    "output_path": str(tmp_path / "map"),
                    "exclude": [],
                }
            }
        }
        mock_resolve.return_value.is_dir.return_value = True

        # 创建源文件
        source_file = tmp_path / "test.txt"
        source_file.write_text("test")

        # 模拟文件收集
        mock_collect.return_value = {"test.txt": source_file}

        # 模拟 _plan
        with patch("commands.sync._plan", return_value=([(source_file, tmp_path / "map/test.txt")], [])):
            sync()

        # 验证输出
        mock_ui.success.assert_called()


class TestVersionCheck:
    """测试版本检查"""

    @patch("commands.sync.get_config")
    def test_sync_unsupported_version(self, mock_get_config):
        mock_get_config.return_value = {"version": "0.0.1"}

        with pytest.raises(SystemExit) as exc:
            sync()
        assert exc.value.code == 1
