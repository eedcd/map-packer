# 贡献指南

感谢您对本项目的贡献！本指南将帮助您了解如何为项目做贡献。

## 开发环境设置

### 1. Fork 项目

在 GitHub 上 fork 本项目到您的托管空间。

```bash
# 克隆您的 fork
git clone https://github.com/wockkkk/map-packer.git
cd map-packer
```

### 2. 设置开发环境

```bash
# 安装 development 依赖包
pip install -e ".[dev]"

# 或使用 uv
uv add -d pytest pytest-cov mypy black flake8
```

### 3. 运行测试

```bash
# 运行所有单元测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 开发流程

### 1. 创建分支

为每个新功能或修复创建一个独立的分支。

```bash
# 使用有意义的分支名
git checkout -b feature/新特性描述
# 或
git checkout -b fix/问题描述
```

### 2. 代码风格

项目使用以下代码风格工具：

- **Black** - 代码格式化器
- **Flake8** - 代码风格检查
- **Mypy** - 类型检查

请确保修改后的代码符合这些工具的要求：

```bash
# 格式化代码
black src/ tests/

# 运行代码检查
flake8 src/ tests/
mypy src/
```

### 3. 编写测试

- 为新功能编写相应的单元测试
- 确保所有测试通过
- 保持测试独立性和可重复性
- 为测试添加适当的注释

### 4. 提交更改

使用清晰的提交信息：

```bash
# 提交格式：类型: 描述
git commit -m "feat: 添加新的打包格式支持"
git commit -m "fix: 修复 sync 命令中的路径问题"
git commit -m "docs: 更新 README 文档"
git commit -m "test: 添加 help 模块的单元测试"
```

### 5. 推送和创建 Pull Request

```bash
# 推送分支
git push origin feature/新特性描述

# 在 GitHub 上创建 Pull Request
```

## 提交信息规范

### 类型说明

- `feat`: 新功能
- `fix`: 缺陷修复
- `docs`: 文档更改
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具配置

### 示例

```bash
feat: 添加 tar.xz 压缩格式支持

- 在 once 和 pack 命令中添加 tar.xz 支持
- 更新 help 文档
- 添加 tar.xz 压缩测试
```

## 常见任务

### 修改帮助系统

修改 `src/helps/` 目录下的 `.txt` 文件：

```bash
# 编辑特定命令的帮助
vim src/helps/once.txt
```

### 添加新功能

1. 创建或修改对应的命令文件
2. 更新 `src/lib/help.py` 或 `src/helps/` 目录
3. 编写单元测试
4. 更新 README 文档

### 更新配置

- `pyproject.toml`: 项目依赖、构建配置
- `uv.lock`: 锁定依赖版本
- `mmp.json`: 示例配置

## 问题报告

如果您发现 bug 或想要提出新功能，请：

1. 检查 GitHub Issues 中是否已有相关讨论
2. 如果没有，创建新的 Issue
3. 提供详细的复现步骤

## Pull Request 要求

- [x] 代码通过所有测试
- [x] 遵循代码风格规范
- [x] 更新相关文档
- [x] 提交信息清晰明确
- [x] 解决方案针对问题本身

## 代码质量

### 覆盖率目标

- 目标覆盖率：80%
- 命令行工具覆盖率：更高要求

### 类型提示

- 鼓励使用类型提示
- 使用 `# type: ignore` 缓存已有问题的行

## 许可证

通过提交代码，您同意项目的 MIT 许可证。

## 联系方式

- GitHub Issues: [https://github.com/wockkkk/map-packer/issues](https://github.com/wockkkk/map-packer/issues)
- 项目负责人关注 issue 和 PR

---

再次感谢您的贡献！您的帮助使这个项目变得更好。
