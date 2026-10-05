"""Unit tests for init command"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from commands.init import init, DEFAULT_CONFIG


class TestInitialize:
    """测试初始化命令"""

    @patch("commands.init.ui")
    @patch("commands.init.Path.exists")
    @patch("subprocess.run")
    def test_init_existing_config(self, mock_subprocess, mock_exists, mock_ui):
        """测试配置已存在的情况"""
        mock_exists.return_value = True

        with pytest.raises(SystemExit) as exc:
            init()
        assert exc.value.code == 1
        mock_ui.error.assert_called()

    @patch("commands.init.ui")
    @patch("commands.init.Path.exists")
    @patch("subprocess.run")
    def test_init_git_unavailable(self, mock_subprocess, mock_exists, mock_ui):
        """测试 git 不可用的情况"""
        mock_exists.return_value = False
        mock_subprocess.returncode = 1

        # 使用 temp 目录避免修改当前工作区
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("lib.ui.console"):
                try:
                    init()
                except SystemExit:
                    pass
        # 验证 git 被跳过
        mock_ui.phase.assert_any_call("Git", "skipped · git not available")

    @patch("commands.init.ui")
    @patch("commands.init.Path.exists")
    @patch("subprocess.run")
    @patch("pathlib.Path.mkdir")
    def test_init_success(self, mock_mkdir, mock_subprocess, mock_exists, mock_ui):
        """测试成功初始化"""
        mock_exists.return_value = False
        mock_subprocess.returncode = 0

        # 使用 temp 目录
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # 模拟交互式输入
            with patch("lib.ui.console"):
                with patch("typer.prompt", return_value="/tmp/world"):
                    try:
                        # 临时更改 CWD
                        old_cwd = Path.cwd()
                        Path(tmpdir).chdir()
                        init()
                        Path(old_cwd).chdir()
                    except SystemExit:
                        pass
            # 验证 git 被初始化
            mock_ui.phase.assert_any_call("Git", "initialized repository")
            # 验证配置被创建
            mock_ui.phase.assert_any_call("Config", mock.ANY)
            # 验证工作流被创建
            mock_ui.phase.assert_any_call("Workflow", mock.ANY)

    @patch("commands.init.ui")
    @patch("commands.init.Path.exists")
    @patch("subprocess.run")
    @patch("pathlib.Path.mkdir")
    def test_init_save_path_validation(self, mock_mkdir, mock_subprocess, mock_exists, mock_ui):
        """测试存档路径验证"""
        mock_exists.return_value = False
        mock_subprocess.returncode = 0

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("lib.ui.console"):
                with patch("typer.prompt", return_value="/nonexistent/path"):
                    try:
                        Path(tmpdir).chdir()
                        init()
                    except SystemExit as e:
                        assert e.code == 1
                        mock_ui.error.assert_called()
                    Path(tmpdir).rm()


class TestInvalidFormat:
    """测试无效格式"""

    @patch("commands.init.ui")
    @patch("commands.init.Path.exists")
    @patch("subprocess.run")
    def test_init_no_save_path(self, mock_subprocess, mock_exists, mock_ui):
        """测试没有输入存档路径"""
        mock_exists.return_value = False
        mock_subprocess.returncode = 0

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("lib.ui.console"):
                with patch("typer.prompt", return_value="   "):
                    try:
                        Path(tmpdir).chdir()
                        init()
                    except SystemExit as e:
                        assert e.code == 1
                        mock_ui.error.assert_called()
