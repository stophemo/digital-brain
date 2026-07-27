#!/usr/bin/env python3
"""把 digital-brain-setup 安装到 Codex 或 Claude Code 的个人 Skills 目录。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "digital-brain-setup"
SKILL_SOURCE = REPO_ROOT / SKILL_NAME
IGNORED_NAMES = {".DS_Store", "__pycache__"}


class InstallError(RuntimeError):
    """表示 Skill 无法安全安装。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="安装 Digital Brain Setup Skill；不覆盖已有的不同版本。"
    )
    parser.add_argument(
        "platform",
        choices=("codex", "claude"),
        help="选择要安装到 Codex 还是 Claude Code",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        help="自定义 Skills 根目录；默认使用所选平台的个人目录",
    )
    return parser.parse_args()


def default_skills_dir(platform: str) -> Path:
    if platform == "codex":
        config_root = Path(
            os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
        )
    else:
        config_root = Path(
            os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
        )
    return config_root.expanduser() / "skills"


def resolve_skills_dir(platform: str, supplied: Path | None) -> Path:
    path = supplied.expanduser() if supplied is not None else default_skills_dir(platform)
    if path.exists() and not path.is_dir():
        raise InstallError(f"Skills 路径已存在且不是目录：{path}")
    return path.resolve(strict=False)


def ignored(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part in IGNORED_NAMES for part in relative.parts) or path.suffix == ".pyc"


def package_files(root: Path) -> dict[Path, Path]:
    files: dict[Path, Path] = {}
    for path in root.rglob("*"):
        if ignored(path, root):
            continue
        if path.is_symlink():
            raise InstallError(f"Skill 包不能包含符号链接：{path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise InstallError(f"Skill 包包含不支持的文件类型：{path}")
        files[path.relative_to(root)] = path
    return files


def verify_source() -> None:
    required = (
        SKILL_SOURCE / "SKILL.md",
        SKILL_SOURCE / "LICENSE",
        SKILL_SOURCE / "scripts/init_vault.py",
    )
    if not SKILL_SOURCE.is_dir() or any(not path.is_file() for path in required):
        raise InstallError(f"仓库中的 Skill 包不完整：{SKILL_SOURCE}")
    package_files(SKILL_SOURCE)


def packages_equal(source: Path, installed: Path) -> bool:
    source_files = package_files(source)
    installed_files = package_files(installed)
    if source_files.keys() != installed_files.keys():
        return False
    return all(
        source_files[relative].read_bytes() == installed_files[relative].read_bytes()
        for relative in source_files
    )


def install(skills_dir: Path) -> tuple[Path, bool]:
    target = skills_dir / SKILL_NAME
    if target.is_symlink():
        raise InstallError(f"安装目标不能是符号链接：{target}")
    if target.exists():
        if not target.is_dir():
            raise InstallError(f"安装目标已存在且不是目录：{target}")
        if packages_equal(SKILL_SOURCE, target):
            return target, False
        raise InstallError(
            f"已存在不同版本，拒绝覆盖：{target}\n"
            "请先备份或移走原目录，再重新执行安装。"
        )

    skills_dir.mkdir(parents=True, exist_ok=True)
    temp_root = Path(
        tempfile.mkdtemp(prefix=f".{SKILL_NAME}.install-", dir=str(skills_dir))
    )
    staged = temp_root / SKILL_NAME
    try:
        shutil.copytree(
            SKILL_SOURCE,
            staged,
            ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"),
        )
        if target.exists() or target.is_symlink():
            raise InstallError(f"安装期间目标被占用，拒绝覆盖：{target}")
        os.rename(staged, target)
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)
    return target, True


def main() -> int:
    args = parse_args()
    try:
        verify_source()
        skills_dir = resolve_skills_dir(args.platform, args.skills_dir)
        target, created = install(skills_dir)
    except (InstallError, OSError) as exc:
        print(f"安装失败：{exc}", file=sys.stderr)
        return 1

    state = "安装完成" if created else "已经安装且内容一致"
    print(f"Digital Brain Setup {state}。")
    print(f"平台：{args.platform}")
    print(f"位置：{target}")
    print(f"下一步：完整读取 {target / 'SKILL.md'}，立即开始交互搭建。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
