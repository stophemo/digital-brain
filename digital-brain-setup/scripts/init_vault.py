#!/usr/bin/env python3
"""安全、可重复地初始化一个空 Digital Brain vault。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
RUNTIME_SCRIPTS = (
    "finalize_snapshot.py",
    "record_schema_update.py",
    "validate_vault.py",
)
RULE_FILES = {
    "codex": "AGENTS.md",
    "claude": "CLAUDE.md",
    "gemini": "GEMINI.md",
}


class InitError(RuntimeError):
    """表示初始化前置条件不满足。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在空目录中初始化 Digital Brain，不覆盖任何现有文件。"
    )
    parser.add_argument("vault", type=Path, help="目标 vault 路径")
    parser.add_argument(
        "--agent",
        required=True,
        choices=(*RULE_FILES, "other"),
        help="选择 Agent 规则文件名",
    )
    parser.add_argument(
        "--rule-file",
        help="--agent other 时使用的规则文件名，必须是 vault 根目录下的 .md 文件",
    )
    parser.add_argument(
        "--allow-existing-git",
        action="store_true",
        help="明确允许在已配置 remote 的现有 Git worktree 内初始化",
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
    if path.is_absolute() or path.name != name or path.suffix.lower() != ".md":
        raise InitError("规则文件必须是 vault 根目录下的单个 .md 文件名。")
    if name.casefold() in {"index.md", "log.md"}:
        raise InitError("规则文件名不能与 index.md 或 log.md 冲突。")
    return name


def nearest_existing_path(path: Path) -> Path:
    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return probe


def git_context(path: Path) -> tuple[Path | None, list[str]]:
    probe = nearest_existing_path(path)
    try:
        root_result = subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None, []
    if root_result.returncode != 0:
        return None, []

    root = Path(root_result.stdout.strip()).resolve()
    remote_result = subprocess.run(
        ["git", "-C", str(root), "remote"],
        check=False,
        capture_output=True,
        text=True,
    )
    remotes = [line for line in remote_result.stdout.splitlines() if line.strip()]
    return root, remotes


def verify_inputs() -> None:
    required = [
        ASSETS_DIR / "Schema.md",
        TEMPLATES_DIR / "config.json",
        TEMPLATES_DIR / "index.md",
        TEMPLATES_DIR / "log.md",
        TEMPLATES_DIR / "gitignore",
        *(Path(__file__).resolve().parent / name for name in RUNTIME_SCRIPTS),
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise InitError("Skill 资源不完整：\n- " + "\n- ".join(missing))


def ensure_empty_target(target: Path) -> bool:
    if target.exists() and not target.is_dir():
        raise InitError(f"目标已存在且不是目录：{target}")
    if target.exists() and any(target.iterdir()):
        raise InitError(f"目标目录非空，拒绝覆盖或合并：{target}")
    return target.exists()


def render_template(source: Path, target: Path, date: str) -> None:
    content = source.read_text(encoding="utf-8").replace("{{DATE}}", date)
    target.write_text(content, encoding="utf-8")


def build_tree(root: Path, rule_file: str) -> None:
    directories = (
        ".digital-brain/scripts",
        ".staging",
        "raw",
        "wiki/_meta",
        "wiki/entities/people",
        "wiki/entities/organizations",
        "wiki/entities/systems",
        "wiki/entities/projects",
        "wiki/concepts",
        "wiki/comparisons",
        "wiki/syntheses",
        "wiki/queries",
        "wiki/drafts",
        "wiki/archive",
        "logs/archive",
    )
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=False)

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    schema_source = ASSETS_DIR / "Schema.md"
    schema_target = root / rule_file
    shutil.copy2(schema_source, schema_target)
    state = {
        "version": 1,
        "rule_file": rule_file,
        "schema_sha256": hashlib.sha256(schema_target.read_bytes()).hexdigest(),
    }
    state_path = root / ".digital-brain/state.json"
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    state_path.chmod(0o444)
    render_template(TEMPLATES_DIR / "config.json", root / ".digital-brain/config.json", today)
    render_template(TEMPLATES_DIR / "index.md", root / "index.md", today)
    render_template(TEMPLATES_DIR / "log.md", root / "log.md", today)
    shutil.copy2(TEMPLATES_DIR / "gitignore", root / ".gitignore")

    script_source = Path(__file__).resolve().parent
    for name in RUNTIME_SCRIPTS:
        destination = root / ".digital-brain/scripts" / name
        shutil.copy2(script_source / name, destination)
        destination.chmod(destination.stat().st_mode | 0o111)


def install_atomically(target: Path, rule_file: str, target_existed: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.init-", dir=str(target.parent))
    )
    removed_empty_target = False
    try:
        build_tree(temp_root, rule_file)
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
        verify_inputs()
        rule_file = resolve_rule_file(args.agent, args.rule_file)
        target = args.vault.expanduser().resolve(strict=False)
        target_existed = ensure_empty_target(target)

        git_root, remotes = git_context(target)
        if remotes and not args.allow_existing_git:
            names = ", ".join(remotes)
            raise InitError(
                f"目标位于已有 Git worktree {git_root}，且配置了 remote：{names}。"
                "请先确认隐私风险；明确同意后再使用 --allow-existing-git。"
            )

        install_atomically(target, rule_file, target_existed)
    except (InitError, OSError) as exc:
        print(f"初始化失败：{exc}", file=sys.stderr)
        return 1

    print("Digital Brain 初始化完成。")
    print(f"vault: {target}")
    print(f"规则文件: {rule_file}")
    if git_root:
        print(f"父 Git worktree: {git_root}")
    print("未执行 git init，未添加 remote，未写入任何来源资料。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
