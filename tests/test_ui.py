"""Unit tests for UI module"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from lib.ui import (
    console,
    header,
    panel,
    phase,
    success,
    error,
    blank,
    format_size,
    size_delta,
)


class TestConsole:
    """测试 Rich console"""

    def test_console_output(self):
        """验证 console 对象存在"""
        assert hasattr(console, "print")
        assert hasattr(console, "status")


class TestHeader:
    """测试头部显示"""

    @patch("lib.ui.console")
    def test_header_basic(self, mock_console):
        header("init", "Initialize repository")
        calls = [call[0][0] for call in mock_console(print_).call_args_list]
        assert any("init" in c for c in calls)


class TestPanel:
    """测试面板显示"""

    @patch("lib.ui.console")
    def test_panel_basic(self, mock_console):
        pairs = [("Key1", "Value1"), ("Key2", "Value2")]
        panel("Title", pairs)
        # 验证面板被创建
        assert any("Title" in str(call) for call in mock_console.print.call_args_list)


class TestPhase:
    """测试阶段显示"""

    @patch("lib.ui.console")
    def test_phase_basic(self, mock_console):
        phase("Phase", "Description")
        assert any("Phase" in str(call) for call in mock_console.print.call_args_list)


class TestSuccess:
    """测试成功消息"""

    @patch("lib.ui.console")
    def test_success(self, mock_console):
        success("Operation completed")
        assert any("Operation completed" in str(call) for call in mock_console.print.call_args_list)


class TestError:
    """测试错误消息"""

    @patch("lib.ui.console")
    def test_error_basic(self, mock_console):
        error("File not found", hint="Check the path")
        assert any("File not found" in str(call) for call in mock_console.print.call_args_list)
        assert any("Check the path" in str(call) for call in mock_console.print.call_args_list)


class TestBlank:
    """测试换行"""

    @patch("lib.ui.console")
    def test_blank(self, mock_console):
        blank()
        assert mock_console.print.call_count == 1


class TestFormatSize:
    """测试大小格式化"""

    def test_format_size_bytes(self):
        assert format_size(1024) == "1.0 KB"
        assert format_size(512) == "512 B"
        assert format_size(0) == "0 B"

    def test_format_size_kilobytes(self):
        assert format_size(1024 * 1024) == "1.0 KB"
        assert format_size(2 * 1024) == "2.0 KB"

    def test_format_size_megabytes(self):
        assert format_size(1024 * 1024 * 1024) == "1.0 MB"

    def test_format_size_gigabytes(self):
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.0 GB"


class TestSizeDelta:
    """测试体积变化"""

    def test_size_delta_shrink(self):
        result = size_delta(1000, 500)
        assert "↓" in result
        assert "smaller" in result

    def test_size_delta_expand(self):
        result = size_delta(500, 1000)
        assert "↑" in result
        assert "larger" in result

    def test_size_delta_same(self):
        result = size_delta(1000, 1000)
        assert "unchanged" in result

    def test_size_delta_zero_before(self):
        result = size_delta(0, 500)
        assert "n/a" in result
