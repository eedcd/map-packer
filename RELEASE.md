# 发布指南

本文档描述了 map-packer 项目的发布流程和步骤。

## 发布准备

### 1. 确保测试通过

在发布前，确保所有测试通过：

```bash
pytest tests/ -v --cov=src --cov-report=html
```

### 2. 更新版本号

更新 `pyproject.toml` 中的版本号：

```toml
version = "0.1.2"  # 更新版本号
```

### 3. 更新 `CHANGELOG.md`

本项目的变更日志采用 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 格式。

```markdown
## [0.1.2] - 2024-01-15
### Changed
- 优化帮助系统显示

### Added
- 添加 tar.xz 压缩格式支持

### Fixed
- 修复 once 命令的参数解析

## [0.1.1] - 2024-01-01
[之前的变更日志]
```

## 发布到 PyPI

### 1. 构建包

```bash
# 使用 Pip
pip install -U build
python -m build

# 或使用 uv
pip install -U uv
uv build
```

### 2. 验证构建

检查生成的包：

```bash
ls -lh dist/
```

应该出现：
- `map_packer-0.1.2.tar.gz`
- `map_packer-0.1.2-py3-none-any.whl`

### 3. 上传到 PyPI

```bash
# 上传到 PyPI (正式环境)
pip upload dist/*

# 或使用 uv
uv publish dist/*

# 上传到 TestPyPI (测试环境，可选)
twine upload --repository testpypi dist/*
```

**注意**：需要先配置 PyPI API Token。

### 4. 测试安装

在干净的环境中测试安装：

```bash
pip uninstall map-packer
pip install -e .  # 本地测试
# 或
pip install map-packer==0.1.2
```

## 发布 GitHub Release

### GitHub Actions 自动发布

项目已配置 GitHub Actions，在推送标签时自动发布：

```bash
# 创建标签
git tag v0.1.2
git push origin v0.1.2
```

GitHub Actions 会自动：
1. 运行测试
2. 构建并上传到 PyPI
3. 创建 GitHub Release
4. 上传构建产物到 release

### 手动发布

如果自动发布失败，可以手动执行：

```bash
# 1. 使用 GitHub CLI
gh release create v0.1.2 \
  --title "map-packer v0.1.2" \
  --generate-notes \
  dist/*

# 2. 上传到 PyPI
twine upload dist/*
```

## 发布检查清单

### 构建前

- [ ] 所有测试通过
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] 文档已更新（README、使用案例等）

### 构建后

- [ ] 包体积合理
- [ ] 不包含敏感信息
- [ ] 元数据正确（名称、版本、描述等）

### 发布后

- [ ] PyPI 页面显示正确
- [ ] GitHub Release 创建成功
- [ ] 从新环境中测试安装
- [ ] 通知社区（如果适用）

## 回滚流程

如果发布后发现严重问题：

1. 从 PyPI 下架错误版本：
   ```bash
   pip uninstall map-packer
   # PyPI 提供下架功能
   ```

2. 修复问题并重新发布新版本

3. 在 GitHub 删除错误的 tag 和 release

## 版本管理策略

本项目遵循 [Semantic Versioning 2.0.0](https://semver.org/)：

- **主版本号 (Major)**: 不兼容的 API 变更
- **次版本号 (Minor)**: 向下兼容的功能添加
- **修订号 (Patch)**: 向下兼容的问题修复

### 示例版本序列

```
0.1.0 → 初始版本
0.1.1 → 小修复
0.1.2 → 小改进
0.2.0 → 新的公开 API
1.0.0 → 稳定发布
```

## 常见问题

### Q: 需要手动创建 release 吗？
A: 不需要。GitHub Actions 会自动创建，前提是您配置好。

### Q: 如何更新 PyPI 依赖？
A: 在 CI/CD 中自动完成。

### Q: 如何在正式发布前测试？
A: 先发布到 TestPyPI 测试。

### Q: 如何创建 `uv.lock`？
A: 运行 `uv lock` 即可生成。

## 相关工具

- **pip**: 包安装工具
- **twine**: PyPI 上传工具
- **uv**: 快速包管理工具
- **gh**: GitHub CLI

---

祝您发布顺利！
