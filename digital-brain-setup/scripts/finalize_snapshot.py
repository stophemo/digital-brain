#!/usr/bin/env python3
"""把已审核的 staging 目录冻结为不可变 raw snapshot。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SnapshotError(RuntimeError):
    """表示快照不满足冻结条件。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="校验 staging 内容、生成 manifest，并原子移动到 raw。"
    )
    parser.add_argument("--vault", required=True, type=Path, help="vault 根目录")
    parser.add_argument(
        "--staging",
        required=True,
        type=Path,
        help="位于 <vault>/.staging/ 下的待冻结目录",
    )
    parser.add_argument("--bucket", required=True, help="已注册的 source bucket")
    parser.add_argument("--slug", required=True, help="快照可读短名，小写 kebab-case")
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "url", "connector", "manual"),
        help="来源类型",
    )
    parser.add_argument(
        "--source-locator",
        default="",
        help="稳定且尽量脱敏的来源标识；不必记录本机绝对路径",
    )
    parser.add_argument(
        "--supersedes",
        help="被替代快照的 manifest 相对路径，例如 raw/general/<id>/manifest.json",
    )
    return parser.parse_args()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_name(value: str, field: str) -> None:
    if not NAME_PATTERN.fullmatch(value):
        raise SnapshotError(f"{field} 必须使用小写 kebab-case：{value!r}")
    if len(value) > 64:
        raise SnapshotError(f"{field} 不能超过 64 个字符。")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_role(relative_path: Path) -> str:
    if len(relative_path.parts) > 1 and relative_path.parts[0] == "original":
        return "original"
    if len(relative_path.parts) > 1 and relative_path.parts[0] == "assets":
        return "asset"
    if relative_path.as_posix() == "content.md":
        return "normalized"
    return "derivative"


def contains_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def collect_files(staging: Path) -> list[dict[str, object]]:
    manifest_path = staging / "manifest.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        raise SnapshotError("staging 中已存在 manifest.json；请先移除旧的未冻结 manifest。")

    files: list[dict[str, object]] = []
    for root, dir_names, file_names in os.walk(staging, followlinks=False):
        root_path = Path(root)
        for name in dir_names:
            path = root_path / name
            mode = path.lstat().st_mode
            if contains_control_characters(name):
                raise SnapshotError(f"目录名禁止控制字符：{path}")
            if stat.S_ISLNK(mode):
                raise SnapshotError(f"快照禁止符号链接目录：{path}")
            if not stat.S_ISDIR(mode):
                raise SnapshotError(f"快照禁止特殊目录项：{path}")
        for name in file_names:
            path = root_path / name
            file_stat = path.lstat()
            mode = file_stat.st_mode
            if contains_control_characters(name):
                raise SnapshotError(f"文件名禁止控制字符：{path}")
            if stat.S_ISLNK(mode):
                raise SnapshotError(f"快照禁止符号链接文件：{path}")
            if not stat.S_ISREG(mode):
                raise SnapshotError(f"快照只允许普通文件：{path}")
            if file_stat.st_nlink > 1:
                raise SnapshotError(f"快照禁止硬链接文件：{path}")
            relative = path.relative_to(staging)
            if any(part in {"", ".", ".."} for part in relative.parts):
                raise SnapshotError(f"非法相对路径：{relative}")
            size = path.stat().st_size
            files.append(
                {
                    "path": relative.as_posix(),
                    "role": classify_role(relative),
                    "size": size,
                    "sha256": sha256_file(path),
                }
            )

    files.sort(key=lambda item: str(item["path"]))
    if not files:
        raise SnapshotError("staging 为空，不能冻结快照。")
    return files


def calculate_content_digest(files: list[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for item in files:
        digest.update(str(item["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item["sha256"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(item["size"]).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def load_registered_buckets(vault: Path) -> set[str]:
    config_path = vault / ".digital-brain/config.json"
    try:
        mode = config_path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise SnapshotError(".digital-brain/config.json 必须是普通文件且不能是符号链接。")
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"无法读取有效 config.json：{exc}") from exc
    if not isinstance(config, dict):
        raise SnapshotError("config.json 根节点必须是对象。")
    buckets = config.get("source_buckets")
    if not isinstance(buckets, list) or not buckets:
        raise SnapshotError("config.json 的 source_buckets 必须是非空数组。")
    if any(
        not isinstance(bucket, str)
        or not NAME_PATTERN.fullmatch(bucket)
        or len(bucket) > 64
        for bucket in buckets
    ):
        raise SnapshotError("config.json 含无效 bucket；bucket 必须使用小写 kebab-case。")
    if len(set(buckets)) != len(buckets):
        raise SnapshotError("config.json 的 source_buckets 不能重复。")
    return set(buckets)


def manifest_files_are_valid(manifest_path: Path, manifest: dict[str, object]) -> bool:
    snapshot = manifest_path.parent.resolve()
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        return False
    try:
        manifest_metadata = manifest_path.lstat()
    except OSError:
        return False
    if not stat.S_ISREG(manifest_metadata.st_mode) or manifest_metadata.st_nlink > 1:
        return False
    actual: set[str] = set()
    for current, dir_names, file_names in os.walk(snapshot, followlinks=False):
        current_path = Path(current)
        for name in dir_names:
            metadata = (current_path / name).lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                return False
        for name in file_names:
            path = current_path / name
            metadata = path.lstat()
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink > 1
            ):
                return False
            if path != manifest_path:
                actual.add(path.relative_to(snapshot).as_posix())
    registered: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            return False
        relative_text = entry.get("path")
        if (
            not isinstance(relative_text, str)
            or relative_text in registered
            or contains_control_characters(relative_text)
        ):
            return False
        relative = Path(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            return False
        if entry.get("role") != classify_role(relative):
            return False
        path = snapshot / relative
        try:
            metadata = path.lstat()
        except OSError:
            return False
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink > 1:
            return False
        if entry.get("size") != path.stat().st_size or entry.get("sha256") != sha256_file(path):
            return False
        registered.add(relative.as_posix())

    if calculate_content_digest(entries) != manifest.get("content_digest"):
        return False
    return actual == registered


def manifest_header_is_valid(manifest_path: Path, manifest: dict[str, object]) -> bool:
    created_at = manifest.get("created_at")
    if not isinstance(created_at, str):
        return False
    try:
        timestamp = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (
        timestamp.tzinfo is not None
        and manifest.get("schema_version") == 1
        and manifest.get("snapshot_id") == manifest_path.parent.name
        and manifest.get("bucket") == manifest_path.parent.parent.name
        and isinstance(manifest.get("content_digest"), str)
    )


def find_source_versions(
    raw: Path,
    source_kind: str,
    source_locator: str,
) -> list[tuple[Path, dict[str, object]]]:
    if not raw.is_dir() or (source_kind == "manual" and not source_locator):
        return []
    versions: list[tuple[Path, dict[str, object]]] = []
    manifest_paths: list[Path] = []
    for bucket in raw.iterdir():
        bucket_metadata = bucket.lstat()
        if stat.S_ISLNK(bucket_metadata.st_mode) or not stat.S_ISDIR(bucket_metadata.st_mode):
            continue
        for snapshot in bucket.iterdir():
            snapshot_metadata = snapshot.lstat()
            if stat.S_ISLNK(snapshot_metadata.st_mode) or not stat.S_ISDIR(
                snapshot_metadata.st_mode
            ):
                continue
            manifest_path = snapshot / "manifest.json"
            try:
                manifest_metadata = manifest_path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(manifest_metadata.st_mode) and manifest_metadata.st_nlink == 1:
                manifest_paths.append(manifest_path)
    for manifest_path in manifest_paths:
        manifest = load_manifest(manifest_path)
        if not manifest:
            continue
        source = manifest.get("source")
        if not isinstance(source, dict):
            continue
        if (
            source.get("kind") == source_kind
            and source.get("locator") == source_locator
            and manifest_header_is_valid(manifest_path, manifest)
            and manifest_files_are_valid(manifest_path, manifest)
        ):
            versions.append((manifest_path, manifest))
    return versions


def order_source_versions(
    vault: Path, versions: list[tuple[Path, dict[str, object]]]
) -> list[tuple[Path, dict[str, object]]]:
    if not versions:
        return []
    by_reference = {
        path.relative_to(vault).as_posix(): (path, manifest) for path, manifest in versions
    }
    roots: list[str] = []
    children: dict[str, str] = {}
    for reference, (_, manifest) in by_reference.items():
        source = manifest.get("source")
        if not isinstance(source, dict):
            raise SnapshotError(f"已有来源链的 source 无效：{reference}")
        parent = source.get("supersedes")
        if parent is None:
            roots.append(reference)
            continue
        if not isinstance(parent, str) or parent not in by_reference:
            raise SnapshotError(f"已有来源链包含无效 supersedes：{reference}")
        if parent in children:
            raise SnapshotError(f"已有来源链出现分叉：{parent}")
        children[parent] = reference
    if len(roots) != 1:
        raise SnapshotError("已有来源链必须且只能有一个起点。")

    ordered: list[tuple[Path, dict[str, object]]] = []
    current = roots[0]
    visited: set[str] = set()
    while True:
        if current in visited:
            raise SnapshotError("已有来源链存在循环。")
        visited.add(current)
        ordered.append(by_reference[current])
        child = children.get(current)
        if child is None:
            break
        current = child
    if len(visited) != len(by_reference):
        raise SnapshotError("已有来源链不连续或包含孤立版本。")
    return ordered


def find_duplicate(
    versions: list[tuple[Path, dict[str, object]]], content_digest: str
) -> Path | None:
    if versions:
        manifest_path, manifest = versions[-1]
        if manifest.get("content_digest") == content_digest:
            return manifest_path.parent
    return None


def validate_supersedes(
    vault: Path,
    value: str | None,
    versions: list[tuple[Path, dict[str, object]]],
) -> str | None:
    if not versions:
        if value:
            raise SnapshotError("当前来源没有旧快照，不能使用 --supersedes。")
        return None
    expected_path = versions[-1][0]
    expected = expected_path.relative_to(vault).as_posix()
    if not value:
        raise SnapshotError(
            "同一来源已有不同内容的快照；新版本必须使用 "
            f"--supersedes {expected} 建立演化链。"
        )
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise SnapshotError("--supersedes 必须是 vault 内的相对 manifest 路径。")
    normalized = relative.as_posix()
    if normalized != expected:
        raise SnapshotError(f"--supersedes 必须指向此来源的最新快照：{expected}")
    path = (vault / relative).resolve(strict=False)
    if not is_relative_to(path, (vault / "raw").resolve()):
        raise SnapshotError("--supersedes 必须指向 raw/ 下的 manifest.json。")
    if path.name != "manifest.json" or not path.is_file():
        raise SnapshotError(f"被替代的 manifest 不存在：{relative.as_posix()}")
    return normalized


def make_read_only(snapshot: Path) -> list[str]:
    warnings: list[str] = []
    paths = sorted(snapshot.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    paths.append(snapshot)
    for path in paths:
        try:
            mode = path.stat().st_mode
            path.chmod(mode & ~0o222)
        except OSError as exc:
            warnings.append(f"无法移除写权限 {path}: {exc}")
    return warnings


def resolve_staging(vault: Path, supplied: Path) -> Path:
    staging_root = vault / ".staging"
    if stat.S_ISLNK(staging_root.lstat().st_mode):
        raise SnapshotError("vault/.staging 禁止是符号链接。")
    candidate = supplied.expanduser()
    if not candidate.is_absolute():
        candidate = vault / candidate
    candidate = Path(os.path.abspath(candidate))
    if candidate.is_symlink():
        raise SnapshotError(f"staging 任务目录禁止符号链接：{candidate}")
    candidate = candidate.resolve(strict=True)
    resolved_root = staging_root.resolve(strict=True)
    if candidate == resolved_root or not is_relative_to(candidate, resolved_root):
        raise SnapshotError("--staging 必须是 vault/.staging/ 下的子目录。")
    if not candidate.is_dir():
        raise SnapshotError(f"staging 不是目录：{candidate}")
    return candidate


def main() -> int:
    args = parse_args()
    manifest_path: Path | None = None
    try:
        vault = args.vault.expanduser().resolve(strict=True)
        if not (vault / "raw").is_dir() or not (vault / ".staging").is_dir():
            raise SnapshotError("目标不是有效 vault：缺少 raw/ 或 .staging/。")
        if (vault / "raw").is_symlink() or (vault / ".staging").is_symlink():
            raise SnapshotError("raw/ 与 .staging/ 禁止是符号链接。")
        validate_name(args.bucket, "bucket")
        validate_name(args.slug, "slug")
        source_locator = args.source_locator.strip()
        if args.source_kind != "manual" and not source_locator:
            raise SnapshotError("非 manual 来源必须提供稳定且尽量脱敏的 --source-locator。")
        registered_buckets = load_registered_buckets(vault)
        if args.bucket not in registered_buckets:
            raise SnapshotError(f"bucket 未在 config.json 注册：{args.bucket}")
        staging = resolve_staging(vault, args.staging)

        files = collect_files(staging)
        if args.source_kind == "file":
            original_directory = staging / "original"
            if original_directory.is_symlink() or not original_directory.is_dir() or not any(
                item["role"] == "original" for item in files
            ):
                raise SnapshotError("file 来源必须在 staging/original/ 目录中保留原件副本。")

        content_digest = calculate_content_digest(files)
        versions = order_source_versions(
            vault,
            find_source_versions(vault / "raw", args.source_kind, source_locator),
        )
        duplicate = find_duplicate(versions, content_digest)
        if duplicate:
            print(f"内容与来源均未变化，复用已有快照：{duplicate}")
            return 0

        supersedes = validate_supersedes(vault, args.supersedes, versions)
        now = dt.datetime.now(dt.timezone.utc)
        created_at = now.isoformat(timespec="microseconds").replace("+00:00", "Z")
        identity = hashlib.sha256(
            (args.source_kind + "\0" + source_locator + "\0" + content_digest).encode(
                "utf-8"
            )
        ).hexdigest()[:12]
        snapshot_id = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{args.slug}-{identity}"
        bucket_path = vault / "raw" / args.bucket
        if bucket_path.exists() and (bucket_path.is_symlink() or not bucket_path.is_dir()):
            raise SnapshotError(f"raw bucket 类型无效或是符号链接：{bucket_path}")
        destination = bucket_path / snapshot_id
        if destination.exists():
            raise SnapshotError(f"目标快照已存在，拒绝覆盖：{destination}")

        manifest = {
            "schema_version": 1,
            "snapshot_id": snapshot_id,
            "created_at": created_at,
            "bucket": args.bucket,
            "source": {
                "kind": args.source_kind,
                "locator": source_locator,
                "supersedes": supersedes,
            },
            "content_digest": content_digest,
            "files": files,
        }
        manifest_path = staging / "manifest.json"
        with manifest_path.open("x", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")

        destination.parent.mkdir(parents=True, exist_ok=True)
        os.rename(staging, destination)
        manifest_path = None
        warnings = make_read_only(destination)
    except (SnapshotError, OSError, json.JSONDecodeError) as exc:
        if manifest_path and manifest_path.exists():
            manifest_path.unlink()
        print(f"冻结失败：{exc}", file=sys.stderr)
        return 1

    print(f"快照已冻结：{destination}")
    print(f"snapshot_id: {snapshot_id}")
    print(f"content_digest: {content_digest}")
    for warning in warnings:
        print(f"警告：{warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
