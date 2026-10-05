"""Unit tests for once command"""

import py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from commands.once import (
    _normalize_format,
    _level_range,
    _collect_files,
    _write_zip,
    _write_tar,
    once,
)


class TestNormalizeFormat:
    """测试格式归一化"""

    def test_normalize_valid(self):
        assert _normalize_format("ZiP") == "zip"
        assert _normalize_format("TAR.GZ") == "tar.gz"
        assert _normalize_format("tgz") == "tar.gz"
        assert _normalize_format("tar") == "tar"
        assert _normalize_format("invalid") == "invalid"


class TestLevelRange:
    """测试压缩等级范围"""

    def test_level_range_tar(self):
        assert _level_range("tar") is None

    def test_level_range_tar_gz(self):
        assert _level_range("tar.gz") == (0, 9)

    def test_level_range_tar_bz2(self):
        assert _level_range("tar.bz2") == (1, 9)


class TestCollectFiles:
    """测试文件收集"""

    def test_collect_files_empty_dir(self, tmp_path):
        files = _collect_files(tmp_path)
        assert files == []

    def test_collect_files_with_files(self, tmp_path):
        # 创建文件
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")

        files = _collect_files(tmp_path)
        assert len(files) == 3
        assert all(f[1].startswith("file") or f[1].startswith("subdir") for f in files)


class TestWriteZip:
    """测试 ZIP 写入"""

    def test_write_zip_level_0(self, tmp_path, capsys):
        target = tmp_path / "test.zip"
        files = [(tmp_path / "test.txt", "test.txt")]
        level = 0

        # Mock pathlib.Path methods
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("zipfile.ZipFile") as mock_zip:
                mock_zip.return_value.__enter__.return_value = MagicMock()
                _write_zip(target, files, level, lambda: None)

        mock_zip.return_value.__enter__.assert_called()
        assert mock_zip.call_args[0][1] == "w"
        assert mock_zip.call_args[0][2] == 0

    def test_write_zip_level_6(self, tmp_path):
        target = tmp_path / "test.zip"
        files = [(tmp_path / "test.txt", "test.txt")]
        level = 6

        with patch("zipfile.ZipFile") as mock_zip:
            mock_zip.return_value.__enter__.return_value = MagicMock()
            _write_zip(target, files, level, lambda: None)

        assert mock_zip.call_args[0][2] == "ZIP_DEFLATED"
        assert mock_zip.return_value.__enter__.return_value.write.call_count == 1


class TestWriteTar:
    """测试 TAR 写入"""

    def test_write_tar_formats(self, tmp_path):
        target = tmp_path / "test.tar.gz"
        files = [(tmp_path / "test.txt", "test.txt")]
        level = 6

        with patch("tarfile.open") as mock_tar:
            mock_tar.return_value.__enter__.return_value = MagicMock()
            _write_tar(target, "tar.gz", files, level, lambda: None)

        assert mock_tar.call_args[0][1] == "w:gz"
        assert mock_tar.return_value.__enter__.return_value.add.call_count == 1


class TestOnceCommand:
    """测试一次性打包命令"""

    @patch("commands.once.ui")
    @patch("commands.once.get_config")
    @patch("commands.once.Path.exists")
    @patch("commands.once.Path.is_dir")
    def test_once_missing_input(self, mock_is_dir, mock_exists, mock_get_config, mock_ui):
        """测试缺少输入路径"""
        mock_exists.return_value = False
        mock_is_dir.return_value = False

        # 调用时不传 input_path
        with pytest.raises(SystemExit) as exc:
            once(
                input_path=None,
                output="test.zip",
                format="zip",
                level=6,
                minify=False,
            )
        assert exc.value.code == 1
        mock_ui.error.assert_called()

    @patch("commands.once.ui")
    @patch("commands.once.get_config")
    @patch("commands.once.Path.exists")
    @patch("commands.once.Path.is_dir")
    def test_once_missing_output(self, mock_is_dir, mock_exists, mock_get_config, mock_ui):
        """测试缺少输出路径"""
        mock_exists.return_value = False
        mock_is_dir.return_value = True
        # 创建临时文件
        Path("temp.txt").write_text("test")

        with pytest.raises(SystemExit) as exc:
            once(
                input_path=str(Path(__file__).parent / "temp.txt"),
                output=None,
                format="zip",
                level=6,
                minify=False,
            )
        assert exc.value.code == 1
        mock_ui.error.assert_called()

    @patch("commands.once.ui")
    @patch("commands.once.get_config")
    @patch("commands.once.Path.exists")
    @patch("commands.once.Path.is_dir")
    def test_once_invalid_format(self, mock_is_dir, mock_exists, mock_get_config, mock_ui):
        """测试无效的格式"""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        Path("test.txt").write_text("test")
        Path("test.zip").unlink(missing_ok=True)

        with pytest.raises(SystemExit) as exc:
            once(
                input_path="test.txt",
                output="test.zip",
                format="invalid",
                level=6,
                minify=False,
            )
        assert exc.value.code == 1
        mock_ui.error.assert_called()

    @patch("commands.once.ui")
    @patch("commands.once.get_config")
    @patch("commands.once.Path.exists")
    @patch("commands.once.Path.is_dir")
    def test_once_invalid_level(self, mock_is_dir, mock_exists, mock_get_config, mock_ui):
        """测试无效的压缩等级"""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        Path("test.txt").write_text("test")
        Path("test.zip").unlink(missing_ok=True)

        with pytest.raises(SystemExit) as exc:
            once(
                input_path="test.txt",
                output="test.zip",
                format="zip",
                level=10,
                minify=False,
            )
        assert exc.value.code == 1
        mock_ui.error.assert_called()

    @patch("commands.once.minify_datapacks")
    @patch("commands.once._collect_files")
    @patch("commands.once.Path.exists")
    @patch("commands.once.Path.is_dir")
    @patch("commands.once.ui")
    @patch("commands.once.get_config")
    @patch("commands.once.Path.parent")
    @patch("pathlib.Path.mkdir")
    def test_once_successful(self, mock_mkdir, mock_parent, mock_get_config, mock_ui,
                              mock_is_dir, mock_exists, mock_collect, mock_minify, tmp_path, capsys):
        """测试成功的打包流程"""
        mock_is_dir.return_value = True
        mock_exists.return_value = False

        # 创建测试文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # 模拟文件收集
        mock_collect.return_value = [(test_file, "test.txt")]

        # 模拟 minify
        mock_minify.return_value = (0, 0)

        # 模拟 _write_zip
        def mock_write_zip(target, files, level, advance):
            # 创建一个空的 zip 文件
            import zipfile
            with zipfile.ZipFile(target, 'w') as zf:
                for f, rel in files:
                    zf.write(f, arcname=rel)

        with patch("commands.once._write_zip", side_effect=mock_write_zip):
            # 调用命令
            once(
                input_path=str(tmp_path),
                output="test.zip",
                format="zip",
                level=6,
                minify=True,
            )

        # 验证输出
        assert Path("test.zip").exists()
        # 模拟验证输出
        captured = capsys.readouterr()
        assert "Pack complete" in captured.out
