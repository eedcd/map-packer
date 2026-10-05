# map-packer (mmp)

[![PyPI - Version](https://img.shields.io/pypi/v/map-packer.svg)](https://pypi.org/project/map-packer/)
[![PyPI - License](https://img.shields.io/pypi/l/map-packer.svg)](https://pypi.org/project/map-packer/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/map-packer.svg)](https://pypi.org/project/map-packer/)
[![Test Status](https://github.com/wockkkk/map-packer/actions/workflows/ci.yml/badge.svg)](https://github.com/wockkkk/map-packer/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/wockkkk/map-packer/branch/main/graph/badge.svg?token=map-packer)](https://codecov.io/gh/wockkkk/map-packer)

一个用于 Minecraft 地图打包的命令行工具，支持世界同步、数据精简、格式压缩和一键发布。

## 特性

- 📦 **智能同步**：同步 Minecraft 世界存档到目标目录，自动忽略指定文件
- 🗑️ **世界优化**：剔除无效区块文件，擦除区块缓存，减小世界体积
- 📁 **格式压缩**：支持 zip、tar、tar.gz 等多种压缩格式
- 🎯 **数据精简**：可选精简 datapack，去除注释和空行，压缩 JSON 格式
- 🏷️ **版本管理**：自动根据名称、时间戳生成版本化存档名
- ⚡ **一次性打包**：`mmp once` 命令适合单次使用或 CI/CD 场景
- 📚 **完整帮助**：`mmp help` 提供所有命令的详细文档

## 安装

```bash
# 使用 pip 安装
pip install map-packer

# 或使用 uv 安装
uv add map-packer

# 验证安装
mmp --version
```

## 使用样例

### 快速打包

一次性打包命令，无需配置：

```bash
# 基本用法
mmp once /path/to/map -o ./output.zip

# 指定格式和压缩级别
mmp once ./map -o ./release.tar.gz -f tar.gz -l 9

# 包含数据精简
mmp once ./map -o ./result.zip
```

### 完整工作流

如果你需要版本化管理，使用完整流程：

```bash
# 初始化项目 (交互式输入存档路径)
mmp init

# 同步世界存档到 map 目录
mmp sync

# 打包为版本化的压缩文件
mmp pack
```

在 `mmp init` 时，系统会提示你输入 Minecraft 存档目录。路径会被保存到 `mmp.json` 中，下次运行 `mmp sync` 直接使用即可。

最终生成的压缩文件位于 `./dist` 目录，随时可以分发或发布到 GitHub 发行版。

## 命令文档

### `mmp help` - 显示帮助信息

```bash
mmp help              # 显示主帮助
mmp help <command>    # 显示特定命令详情
```

### `mmp init` - 初始化项目

在当前位置创建 mmp 项目：

- 自动执行 `git init`（如果 git 可用）
- 交互式询问存档路径并保存到 `mmp.json`
- 生成 `mmp.json` 默认配置
- 创建 `.github/workflows/pack.yml`（用于 GitHub 发布）
- 创建地图输出目录

```bash
mmp init
```

### `mmp sync` - 同步世界

将 Minecraft 存档同步到项目目录：

- 从 `mmp.json` 的 `data.sync.save_path` 读取源世界
- 根据 `mmp.json` 配置忽略规则
- 可选剔除未使用区块和优化缓存

```bash
mmp sync [-c <config>]
```

### `mmp pack` - 版本化打包

将地图打包为带版本的压缩文件：

- 使用 `mmp.json` 中的 `data.pack` 配置
- 输出文件名格式：`{name} {date}-{hash}`
- 自动记录体积变化
- 支持数据精简

```bash
mmp pack [-c <config>]
```

### `mmp once` - 快速打包

一次性打包命令，无需配置：

- 直接指定输入目录和输出文件
- 快速打包而不依赖配置文件

使用方式:
```bash
mmp once <input-path> -o <output-path>

选项:
  -o, --output    输出文件路径
  -f, --format    压缩格式 (zip, tar, tar.gz, tar.bz2, tar.xz)
  -l, --level     压缩级别 (0-9, 0 为不压缩)
  -m, --minify    精简 datapack（默认： true）

示例:
  mmp once /path/to/map -o ./output.zip
  mmp once ./map -o ./release.tar.gz -f tar.gz -l 9
```

## TODO

- [ ] 添加 JPEG/PNG 转换
- [ ] 支持更复杂的数据包优化
- [ ] 添加预构建版和 Docker 部署
- [ ] 支持远程世界目录同步

## 贡献指南

欢迎参与项目贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何为项目做贡献。

### 开发设置

```bash
# 克隆项目
git clone https://github.com/wockkkk/map-packer.git
cd map-packer

# 安装开发依赖
uv add -d pytest pytest-cov
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式化

```bash
black src/ tests/
flake8 src/ tests/
```

## 许可证

本项目采用 [MIT 许可证](LICENSE) - 详见 [LICENSE](LICENSE) 文件。

## 更新历史

### [0.1.1] - 2024-01-15

- ✨ 添加 `mmp help` 和 `mmp once` 命令
- 🔄 移除 `.env` 依赖，改为交互式输入
- 📚 完善帮助系统和文档
- ✅ 添加完整单元测试覆盖
- 🚀 配置 GitHub Actions CI/CD

### [0.1.0] - 2024-01-01

- 初始版本发布


## 特性

- 📦 **智能同步**：同步 Minecraft 世界存档到目标目录，自动忽略指定文件
- 🗑️ **世界优化**：剔除无效区块文件，擦除区块缓存，减小世界体积
- 📁 **格式压缩**：支持 zip、tar、tar.gz 等多种压缩格式
- 🎯 **数据精简**：可选精简 datapack，去除注释和空行，压缩 JSON 格式
- 🏷️ **版本管理**：自动根据名称、时间戳生成版本化存档名
- ⚡ **一次性打包**：`mmp once` 命令适合单次使用或 CI/CD 场景
- 📚 **完整帮助**：`mmp help` 提供所有命令的详细文档

## 安装

```bash
# 使用 pip 安装
pip install map-packer

# 验证安装
mmp --version
```

## 使用样例

### 快速打包

一次性打包命令，无需配置：

```bash
# 基本用法
mmp once /path/to/map -o ./output.zip

# 指定格式和压缩级别
mmp once ./map -o ./release.tar.gz -f tar.gz -l 9

# 包含数据精简
mmp once ./map -o ./result.zip
```

### 完整工作流

如果你需要版本化管理，使用完整流程：

```bash
# 初始化项目 (交互式输入存档路径)
mmp init

# 同步世界存档到 map 目录
mmp sync

# 打包为版本化的压缩文件
mmp pack
```

在 `mmp init` 时，系统会提示你输入 Minecraft 存档目录。路径会被保存到 `mmp.json` 中，下次运行 `mmp sync` 直接使用即可。

最终生成的压缩文件位于 `./dist` 目录，随时可以分发或发布到 GitHub 发行版。

## 命令文档

### `mmp help` - 显示帮助信息

```bash
mmp help              # 显示主帮助
mmp help <command>    # 显示特定命令详情
```

### `mmp init` - 初始化项目

在当前位置创建 mmp 项目：

- 自动执行 `git init`（如果 git 可用）
- 交互式询问存档路径并保存到 `mmp.json`
- 生成 `mmp.json` 默认配置
- 创建 `.github/workflows/pack.yml`（用于 GitHub 发布）
- 创建地图输出目录

```bash
mmp init
```

### `mmp sync` - 同步世界

将 Minecraft 存档同步到项目目录：

- 从 `mmp.json` 的 `data.sync.save_path` 读取源世界
- 根据 `mmp.json` 配置忽略规则
- 可选剔除未使用区块和优化缓存

```bash
mmp sync [-c <config>]
```

### `mmp pack` - 版本化打包

将地图打包为带版本的压缩文件：

- 输出文件名格式：`{name} {date}-{hash}`
- 自动记录体积变化
- 支持数据精简

```bash
mmp pack [-c <config>]
```

### `mmp once` - 一次性打包

与 `mmp pack` 类似但输出固定文件名：

- 输出文件名：`{map-name}.{format}`
- 适合 CI/CD 或单次使用场景

```bash
mmp once [-c <config>]
```

## 配置文件

### `mmp.json`

MMP 的核心配置文件，包含项目的基本信息和命令选项：

```json
{
  "version": "0.0.2",
  "name": "my-map",
  "data": {
    "sync": {
      "output_path": "./map",
      "optimize": true,
      "prune": true,
      "exclude": ["session.lock"]
    },
    "pack": {
      "input_path": "./map",
      "output_path": "./dist",
      "name": "{name} {date}-{hash}",
      "format": "zip",
      "compression_level": 6,
      "minify_datapack": true
    }
  }
}
```

### 配置项说明

**同步选项** (`data.sync`)：

- `save_path` - 存档目录路径 (首次通过 `mmp init` 设置)
- `output_path` - 同步目标目录 (默认: `./map`)
- `optimize` - 优化区块缓存 (默认: `true`)
- `prune` - 剔除未使用区块 (默认: `true`)
- `exclude` - 忽略规则列表

**打包选项** (`data.pack`)：

- `input_path` - 打包源目录 (默认: `./map`)
- `output_path` - 输出目录 (默认: `./dist`)
- `name` - 归档名称模板 (支持 `{name}`, `{date}`, `{time}`, `{hash}` 等)
- `format` - 压缩格式 (zip/tar/tar.gz/tar.bz2/tar.xz)
- `compression_level` - 压缩等级 (0-9)
- `minify_datapack` - 精简 datapack 数据

## GitHub Actions 集成

`mmp init` 会生成 `.github/workflows/pack.yml`，实现自动打包发布：

- 每次推送自动打包地图
- 直接发布为 GitHub Release
- 支持自定义配置

## 依赖格式说明

### 打包格式

| 格式 | 扩展名 | 压缩等级 |
|------|--------|----------|
| zip | .zip | 0-9 |
| tar | .tar | n/a |
| tar.gz | .tar.gz | 0-9 |
| tar.bz2 | .tar.bz2 | 1-9 |
| tar.xz | .tar.xz | 0-9 |

### 名称模板占位符

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{name}` | 地图名称 | my-map |
| `{date}` | 日期 (YYYYMMDD) | 20240115 |
| `{time}` | 时间 (HHMMSS) | 143056 |
| `{datetime}` | 日期时间 | 20240115143056 |
| `{timestamp}` | Unix 时间戳 | 1705328456 |
| `{hash}` | 时间戳 SHA-256 前 6 位 | a1b2c3 |

## 错误处理

- 所有命令遇到错误会提供详细的修复建议
- 使用 `--config` 指定自定义配置文件
- 错误信息使用彩色输出，在终端阅读更清晰

## CLI 颜色主题

- **品牌色** (cyan) - 主要元素和标题
- **成功** (green) - 完成状态
- **错误** (red) - 失败状态
- **数值** (yellow) - 数字和统计
- **路径** (cyan) - 文件路径

## 开发

本项目使用以下工具：

- [uv](https://github.com/astral-sh/uv) - 依赖管理和包安装
- [Typer](https://github.com/tiangolo/typer) - CLI 框架
- [Rich](https://github.com/Textualize/rich) - 终端 UI

[更多问题？查看 PyPI 上的项目详情](https://pypi.org/project/map-packer/)

贡献指南：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m '添加 Amazing 功能'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 提交 Pull Request

## 许可证

[MIT License](LICENSE)

## 更新历史

- **v0.1.0** - 初始版本
