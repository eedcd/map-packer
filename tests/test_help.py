"""Unit tests for lib/help module"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 确保可以导入 src 中的模块
from lib.help import (
    HELPS_DIR,
    _load_help_file,
    get_command_help,
    show_help,
)


class TestLoadHelpFile:
    """测试帮助文件加载功能"""

    @patch("lib.help.HELPS_DIR")
    def test_load_success(self, mock_helper):
        mock_path = Path("/mock/help.txt")
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "Help content"

        result = _load_help_file("test")
        assert result == "Help content"
        mock_path.exists.assert_called_once()
        mock_path.read_text.assert_called_once()

    @patch("lib.help.HELPS_DIR")
    def test_load_missing_file(self, mock_helper):
        mock_path = Path("/mock/missing.txt")
        mock_path.exists.return_value = False

        result = _load_help_file("missing")
        assert result is None

    @patch("lib.help.HELPS_DIR")
    def test_load_exception(self, mock_helper):
        mock_path = Path("/mock/help.txt")
        mock_path.exists.return_value = True
        mock_path.read_text.side_effect = Exception("IO error")

        result = _load_help_file("test")
        assert result is None


class TestGetCommandHelp:
    """测试获取命令帮助功能"""

    @patch("lib.help._load_help_file")
    def test_get_command_help_success(self, mock_load):
        mock_load.return_value = "Title\n\nContent goes here"
        result = get_command_help("init")
        assert result is not None
        title, content = result
        assert title == "Title"
        assert content.strip() == "Content goes here"

    @patch("lib.help._load_help_file")
    def test_get_command_help_missing(self, mock_load):
        mock_load.return_value = None
        result = get_command_help("unknown")
        assert result is None


class TestShowHelp:
    """测试显示帮助功能"""

    @patch("lib.help.console")
    @patch("lib.help.get_command_help")
    def test_show_help_main(self, mock_get, mock_console, capsys):
        mock_get.return_value = None
        # 测试主帮助显示
        show_help()
        mock_console.print.assert_called()

    @patch("lib.help.console")
    @patch("lib.help.get_command_help")
    def test_show_help_specific(self, mock_get, mock_console):
        mock_get.return_value = ("Title", "Content")
        show_help("init")
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        assert any("help init" in c for c in calls)

    @patch("lib.help.console")
    @patch("lib.help.get_command_help")
    def test_show_help_version(self, mock_get, mock_console):
        show_help("version")
        # 版本信息应该被打印
        mock_console.print.assert_called()

    @patch("lib.help.console")
    @patch("lib.help.get_command_help")
    def test_show_help_unknown(self, mock_get, mock_console):
        mock_get.return_value = None
        show_help("unknown")
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        assert any("Unknown command" in c for c in calls)
