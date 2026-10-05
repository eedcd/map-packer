# Map Packer 测试指南

## 快速开始

### 安装测试依赖

```bash
# 使用 pip
pip install -e ".[dev]"

# 或使用 uv
uv add -d pytest pytest-cov
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_help.py -v

# 运行特定测试类
pytest tests/test_help.py::TestLoadHelpFile -v

# 运行特定测试函数
pytest tests/test_help.py::TestLoadHelpFile::test_load_success -v

# 运行单个文件并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 运行测试并过滤掉慢速测试
pytest tests/ -m "not slow"

# 使用自定义测试选项
pytest tests/ -v --tb=line --maxfail=5
```

### 使用运行脚本

```bash
./run_tests.sh
```

## 测试覆盖范围

当前测试覆盖以下模块：

### 1. 帮助系统
- `tests/test_help.py` - lib/help 模块测试
- 测试帮助文件加载、命令帮助显示、版本信息等

### 2. 一次性打包命令
- `tests/test_once.py` - once 命令单元测试
- 测试格式、压缩等级、文件收集、ZIP/TAR 写入等

### 3. 初始化命令
- `tests/test_init.py` - init 命令单元测试
- 测试配置检查、Git 初始化、存档路径验证等

### 4. 同步命令
- `tests/test_sync.py` - sync 命令单元测试
- 测试忽略规则、文件比较、同步计划、版本检查等

### 5. 配置文件
- `tests/test_config.py` - config 模块测试
- 测试 JSON 读取、版本验证等

### 6. UI 模块
- `tests/test_ui.py` - UI 工具测试
- 测试控制台输出、大小格式化等

## 编写新测试

### 基本结构

```python
import pytest

def test_example():
    """测试示例"""
    assert True is True

def test_with_fixture(fixture_name):
    """使用 fixture 的测试"""
    pass

class TestExample:
    """测试类"""
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """慢速测试示例"""
        pass
```

### 使用夹具 (Fixtures)

参考 `tests/conftest.py` 中的定义：

- `tmp_path` - pytest 提供的临时目录
- `sample_config` - 示例配置文件
- `temp_map_dir` - 临时地图目录
- `temp_save_dir` - 临时存档目录
- `mock_console` - Mock 控制台

### 发布测试

```python
def test_publish_config(tmp_path):
    """
    发布测试示例
    """
    # 1. 准备测试数据
    # 2. 执行测试逻辑
    # 3. 验证结果
    pass
```

## 测试覆盖率

- 目标覆盖率：80% +
- 生成 HTML 报告：`pytest --cov-report=html`
- 报告位置：`coverage_html/index.html`
- 阅读 Chrome 浏览器打开报告

## 常见问题

### 测试失败

```bash
# 运行单个测试以获取详细信息
pytest tests/test_help.py::TestLoadHelpFile::test_load_success -vv

# 运行测试并查看覆盖
pytest tests/ --cov=src --cov-report=term-missing
```

### Mock 技巧

```python
from unittest.mock import patch, MagicMock

@patch("module.function")
def test_mocked_function(mock_func):
    mock_func.return_value = "test"
    # 测试被 mock 的函数
```

### 测试特定文件

```bash
# 测试特定函数
pytest tests/test_help.py::TestShowHelp::test_show_help_main

# 测试测试类
pytest tests/test_help.py::TestLoadHelpFile
```

## CI 自动化

GitHub Actions 会在以下情况自动运行测试：
- Push 到 `main` 分支
- Pull Request 到 `main` 分支

## 维护测试

- 添加新测试时要注意边界情况
- 保持测试的独立性和可重复性
- 更新注释和文档
- 定期清理过时的测试

## 贡献指南

### 提交新测试

1. 确认测试用例编号
2. 在 tests/ 目录下创建测试文件
3. 编写清晰的测试和说明
4. 运行 `pytest -v` 确保所有测试通过
5. 提交并推送

### 保持代码质量

```bash
# 运行所有测试
pytest tests/ -v

# 检查覆盖率
pytest tests/ --cov=src --cov-report=html

# 运行 flake8（代码风格）
flake8 src/ tests/

# 运行 mypy（类型检查）
mypy src/ tests/
```

## 许可证

许可：MIT
