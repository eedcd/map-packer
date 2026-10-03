"""初始化命令

把当前目录初始化为一个 mmp 仓库：尝试执行 git init、写入默认的
mmp.json 配置，并创建地图输出目录
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import typer
from rich.markup import escape

from lib import ui

# 默认配置，字段与 sync / pack 命令读取的 data 字段保持一致
DEFAULT_CONFIG = {
    "version": "0.0.2",
    "name": "map",
    "data": {
        "sync": {
            "optimize": True,
            "prune": True,
            "output_path": "./map",
            "exclude": [
                "session.lock",
                "level.dat_old",
            ],
        },
        "pack": {
            "input_path": "./map",
            "output_path": "./dist",
            "name": "{name} {date}-{hash}",
            "format": "zip",
            "compression_level": 6,
            "minify_datapack": True,
        },
    },
}

# 初始化时写入 .gitignore 的内容
GITIGNORE_CONTENT = ".env\ndist\n"

# 初始化时生成的 GitHub Actions 工作流：每次推送自动打包并发布到发行版
WORKFLOW_PATH = Path(".github") / "workflows" / "pack.yml"

WORKFLOW_CONTENT = """\
name: Pack Map

on:
  push:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  pack:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Install map-packer
        run: pip install map-packer

      - name: Pack map
        run: mmp pack

      - name: Resolve archive
        id: archive
        run: |
          archive="$(ls -t dist/* | head -n 1)"
          echo "path=$archive" >> "$GITHUB_OUTPUT"
          echo "name=$(basename "$archive")" >> "$GITHUB_OUTPUT"
          echo "tag=$(basename "$archive" | tr ' ' '-')" >> "$GITHUB_OUTPUT"

      - name: Publish release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release create "${{ steps.archive.outputs.tag }}" \\
            "${{ steps.archive.outputs.path }}" \\
            --title "${{ steps.archive.outputs.name }}" \\
            --notes "$(git log -1 --pretty=%B)"
"""


def _run_git_init(cwd: Path) -> bool:
    """尝试在当前目录执行 git init，成功返回 True

    git 不可用或执行失败时返回 False，由调用方决定如何提示
    """
    if shutil.which("git") is None:
        return False
    try:
        result = subprocess.run(
            ["git", "init"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def init() -> None:
    """Initialize the current directory as an mmp repository.

    Rules:
    - run `git init` in the current directory when git is available;
    - write the default mmp.json when it does not exist yet;
    - generate .github/workflows/pack.yml so every push packs the map and
      publishes the archive to a GitHub release;
    - create the output directory from data.sync.output_path.

    Raises:
        typer.Exit: When mmp.json already exists.
    """
    cwd = Path.cwd()
    config_path = cwd / "mmp.json"

    ui.header("init", "Initialize the current directory as an mmp repository")

    if config_path.exists():
        ui.error(
            f"[path]{escape(str(config_path))}[/path] already exists",
            hint="remove it first to re-initialize",
        )
        raise typer.Exit(code=1)

    # 尝试执行 git init，git 不可用时仅提示，不阻断初始化
    if _run_git_init(cwd):
        ui.phase("Git", "[ok]initialized[/ok] [muted]repository[/muted]")
    else:
        ui.phase("Git", "[muted]skipped · git not available[/muted]")

    # 写入 .gitignore（追加模式，若已有该文件则保留原有内容）
    gitignore_path = cwd / ".gitignore"
    needs_gitignore = False
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        if ".env" not in content.splitlines():
            gitignore_path.write_text(content + GITIGNORE_CONTENT, encoding="utf-8")
            needs_gitignore = True
    else:
        gitignore_path.write_text(GITIGNORE_CONTENT, encoding="utf-8")
        needs_gitignore = True
    if needs_gitignore:
        ui.phase("Gitignore", f"[path].gitignore[/path]")

    # 写入默认配置
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
        f.write("\n")
    ui.phase("Config", f"[path]{escape(str(config_path))}[/path]")

    # 生成 GitHub Actions 工作流：每次推送自动打包并发布到发行版
    workflow_path = cwd / WORKFLOW_PATH
    if workflow_path.exists():
        ui.phase("Workflow", "[muted]skipped · already exists[/muted]")
    else:
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(WORKFLOW_CONTENT, encoding="utf-8")
        ui.phase("Workflow", f"[path]{escape(WORKFLOW_PATH.as_posix())}[/path]")

    # 创建地图输出目录
    output_path = Path(DEFAULT_CONFIG["data"]["sync"]["output_path"])
    target = (cwd / output_path).resolve()
    target.mkdir(parents=True, exist_ok=True)
    ui.phase("Map", f"[path]{escape(str(target))}[/path]")

    ui.blank()
    ui.success("[bold]Initialized mmp repository[/bold]")
