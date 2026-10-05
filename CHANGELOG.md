# 更新日志

本采用 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 格式。

## [0.1.1] - 2024-01-01

### ✨ Added
- 新增 `mmp help` 命令，显示详细的命令帮助信息
- 新增 `mmp once` 命令，实现快速打包而无需版本管理
- 帮助信息移至 `src/helps/` 目录，支持纯文本格式
- 使用 `uv` 进行依赖管理，生成 `uv.lock` 文件
- 添加 GitHub Actions CI 工作流 (`.github/workflows/ci.yml`)
- 添加完整的单元测试覆盖（6 个测试文件）
- 添加测试运行脚本 (`run_tests.sh`)
- 添加依赖和配置文件校验
- 添加 Python 版本兼容检查

### 🔄 Changed
- `mmp init` 改为交互式输入存档路径，保存到 `mmp.json`
- 移除 `.env` 依赖，所有配置集中在 `mmp.json`
- 优化 `mmp sync` 错误处理，改进配置读取
- 改进 `once` 命令的参数验证和错误消息
- 更新 README 文档，添加更多使用示例
- 添加 PyPI 发布徽章和 CI 状态徽章到 README

### 🐛 Fixed
- 修复 `onit` 命令的路径验证问题
- 修复 `sync` 命令的存档路径读取逻辑
- 修复 `help` 命令的中文显示问题
- 修复 `once` 命令的压缩等级验证

### 🧹 Refactored
- 重构帮助系统，将 `lib/help.py` 改为从文件读取
- 将 `help.txt` 移到 `src/helps/` 目录
- 简化 `_load_help_file` 函数，移除冗余后缀尝试
- 优化 `pyproject.toml` 结构，添加 `tool.uv` 和 `tool.pytest` 配置

### 📚 Documentation
- 更新 `README.md`，包含新特性和使用样例
- 创建 `TESTING.md` 测试指南
- 创建 `CONTRIBUTING.md` 贡献指南
- 创建 `RELEASE.md` 发布指南
- 添加 GitHub Actions 说明

### ✅ Testing
- 添加 `tests/test_help.py` - 帮助系统测试
- 添加 `tests/test_once.py` - 一次性打包命令测试
- 添加 `tests/test_init.py` - 初始化命令测试
- 添加 `tests/test_sync.py` - 同步命令测试
- 添加 `tests/test_config.py` - 配置模块测试
- 添加 `tests/test_ui.py` - UI 工具测试
- 添加测试 FIXTURES 和夹具配置文件
- 配置 GitHub Actions 自动化测试

### 🔧 Configuration
- 更新 `pyproject.toml` 添加 pytest 依赖
- 添加 `pytest.ini` 配置文件
- 添加 GitHub Actions 测试工作流
- 添加 `uv.lock` 依赖锁定文件
- 更新 `lib/help.py` 从文件读取帮助

---

## [0.1.0] - 2023-12-01

### ✨ Added
- 初始版本发布
- 基础命令: `init`, `sync`, `pack`
- 配置文件支持
- 单元测试框架基础
- 基本文档

---

[unreleased]: https://github.com/wockkkk/map-packer/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/wockkkk/map-packer/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/wockkkk/map-packer/releases/tag/v0.1.0
