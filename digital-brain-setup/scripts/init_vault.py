#!/usr/bin/env python3
"""在空目录中创建一个轻量、可直接使用的 Digital Brain。"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path
import shutil
import sys
import tempfile


SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
RULE_FILES = {
    "codex": "AGENTS.md",
    "claude": "CLAUDE.md",
    "gemini": "GEMINI.md",
}
RESERVED_FILES = {
    "index.md",
    "profile.md",
    "start-here.md",
}


class InitError(RuntimeError):
    """表示初始化前置条件不满足。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在空目录中初始化 Digital Brain，不覆盖任何现有文件。"
    )
    parser.add_argument("vault", type=Path, help="目标 Digital Brain 路径")
    parser.add_argument(
        "--agent",
        required=True,
        choices=(*RULE_FILES, "other"),
        help="选择主要使用的 Agent",
    )
    parser.add_argument(
        "--rule-file",
        help="--agent other 时使用的规则文件名，必须是根目录下的 .md 文件",
    )
    return parser.parse_args()


def resolve_rule_file(agent: str, custom_name: str | None) -> str:
    if agent == "other":
        if not custom_name:
            raise InitError("--agent other 必须同时提供 --rule-file。")
        name = custom_name
    else:
        if custom_name:
            raise InitError("只有 --agent other 可以使用 --rule-file。")
        name = RULE_FILES[agent]

    path = Path(name)
    if (
        path.is_absolute()
        or path.name != name
        or path.suffix.lower() != ".md"
        or name.startswith(".")
        or any(ord(character) < 32 for character in name)
    ):
        raise InitError("规则文件必须是根目录下安全的单个 .md 文件名。")
    if name.casefold() in RESERVED_FILES:
        raise InitError("规则文件名与 Digital Brain 的基础文件冲突。")
    return name


def verify_assets() -> None:
    required = (
        ASSETS_DIR / "Schema.md",
        TEMPLATES_DIR / "START-HERE.md",
        TEMPLATES_DIR / "profile.md",
        TEMPLATES_DIR / "index.md",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise InitError("Skill 资源不完整：\n- " + "\n- ".join(missing))


def inspect_target(supplied: Path) -> tuple[Path, bool]:
    expanded = supplied.expanduser()
    if expanded.is_symlink():
        raise InitError(f"目标不能是符号链接：{expanded}")

    target = expanded.resolve(strict=False)
    if target.exists() and not target.is_dir():
        raise InitError(f"目标已存在且不是目录：{target}")
    if target.exists() and any(target.iterdir()):
        raise InitError(f"目标目录非空，拒绝覆盖或合并：{target}")
    return target, target.exists()


def render_template(source: Path, target: Path, replacements: dict[str, str]) -> None:
    content = source.read_text(encoding="utf-8")
    for marker, value in replacements.items():
        content = content.replace("{{" + marker + "}}", value)
    target.write_text(content, encoding="utf-8")


def build_vault(root: Path, rule_file: str) -> None:
    for directory in ("inbox", "raw", "wiki"):
        (root / directory).mkdir()

    shutil.copy2(ASSETS_DIR / "Schema.md", root / rule_file)
    today = dt.date.today().isoformat()
    replacements = {
        "DATE": today,
        "RULE_FILE": rule_file,
    }
    for name in ("START-HERE.md", "profile.md", "index.md"):
        render_template(TEMPLATES_DIR / name, root / name, replacements)


def install_atomically(target: Path, rule_file: str, target_existed: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.init-", dir=str(target.parent))
    )
    removed_empty_target = False
    try:
        build_vault(temp_root, rule_file)
        if target_existed:
            target.rmdir()
            removed_empty_target = True
        os.replace(temp_root, target)
    except Exception:
        if temp_root.exists():
            shutil.rmtree(temp_root)
        if removed_empty_target and not target.exists():
            target.mkdir()
        raise


def main() -> int:
    args = parse_args()
    try:
        verify_assets()
        rule_file = resolve_rule_file(args.agent, args.rule_file)
        target, target_existed = inspect_target(args.vault)
        install_atomically(target, rule_file, target_existed)
    except (InitError, OSError) as exc:
        print(f"初始化失败：{exc}", file=sys.stderr)
        return 1

    print("Digital Brain 初始化完成。")
    print(f"位置：{target}")
    print(f"Agent 规则：{rule_file}")
    print("下一步：阅读 START-HERE.md，然后提供第一份资料。")
    print("未创建 Git 仓库，未上传或复制任何用户资料。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
