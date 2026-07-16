#!/usr/bin/env python3
"""在用户已确认 Schema 变更后，记录新的规则文件校验值。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


class StateError(RuntimeError):
    """表示 Schema 状态文件或规则文件无效。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="记录已获用户授权的 Schema 变更；本命令不会修改规则内容。"
    )
    parser.add_argument("vault", nargs="?", default=".", type=Path, help="vault 根目录")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_regular_file(path: Path, label: str) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise StateError(f"无法读取 {label}：{exc}") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink > 1
    ):
        raise StateError(f"{label} 必须是独立普通文件，不能是 symlink 或 hardlink。")
    return metadata


def load_state(path: Path) -> tuple[dict[str, object], os.stat_result]:
    metadata = require_regular_file(path, "state.json")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StateError(f"state.json 不是有效 JSON：{exc}") from exc
    if not isinstance(state, dict) or state.get("version") != 1:
        raise StateError("state.json 根节点或 version 无效。")
    return state, metadata


def resolve_rule(vault: Path, state: dict[str, object]) -> Path:
    rule_name = state.get("rule_file")
    if not isinstance(rule_name, str):
        raise StateError("state.json 的 rule_file 必须是字符串。")
    relative = Path(rule_name)
    if (
        relative.is_absolute()
        or relative.name != rule_name
        or relative.suffix.lower() != ".md"
        or rule_name.casefold() in {"index.md", "log.md"}
    ):
        raise StateError("rule_file 必须是 vault 根目录下的独立 .md 文件。")
    rule = vault / rule_name
    require_regular_file(rule, "Agent 规则文件")
    return rule


def write_state_atomically(
    path: Path, state: dict[str, object], original_metadata: os.stat_result
) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=".state-", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(stat.S_IMODE(original_metadata.st_mode))
        os.replace(temporary, path)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def main() -> int:
    args = parse_args()
    try:
        vault = args.vault.expanduser().resolve(strict=True)
        control = vault / ".digital-brain"
        control_metadata = control.lstat()
        if stat.S_ISLNK(control_metadata.st_mode) or not stat.S_ISDIR(
            control_metadata.st_mode
        ):
            raise StateError(".digital-brain 必须是非链接目录。")
        state_path = control / "state.json"
        state, state_metadata = load_state(state_path)
        rule = resolve_rule(vault, state)
        current_hash = sha256_file(rule)
        previous_hash = state.get("schema_sha256")
        if not isinstance(previous_hash, str) or not re.fullmatch(
            r"[0-9a-f]{64}", previous_hash
        ):
            raise StateError("state.json 的 schema_sha256 格式无效。")
        if current_hash == previous_hash:
            print("Schema 校验值未变化，无需更新。")
            return 0
        state["schema_sha256"] = current_hash
        write_state_atomically(state_path, state, state_metadata)
    except (OSError, StateError) as exc:
        print(f"记录失败：{exc}", file=sys.stderr)
        return 1

    print(f"已记录授权后的 Schema：{rule}")
    print(f"schema_sha256: {current_hash}")
    print("请在 log.md 追加 config 记录，说明变更内容和用户授权。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
