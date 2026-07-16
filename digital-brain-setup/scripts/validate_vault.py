#!/usr/bin/env python3
"""验证 Digital Brain vault 的结构和 raw snapshot 完整性。"""

from __future__ import annotations

import argparse
from collections import defaultdict
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Iterable


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_DIRECTORIES = (
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
REQUIRED_FILES = (
    ".digital-brain/config.json",
    ".digital-brain/state.json",
    ".digital-brain/scripts/finalize_snapshot.py",
    ".digital-brain/scripts/record_schema_update.py",
    ".digital-brain/scripts/validate_vault.py",
    "index.md",
    "log.md",
    ".gitignore",
)
SOURCE_KINDS = {"file", "url", "connector", "manual"}
FILE_ROLES = {"original", "normalized", "asset", "derivative"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: Path | str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warning(self, path: Path | str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 Digital Brain vault。")
    parser.add_argument("vault", nargs="?", default=".", type=Path, help="vault 根目录")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def calculate_content_digest(files: Iterable[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda value: str(value["path"])):
        digest.update(str(item["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item["sha256"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(item["size"]).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def contains_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def expected_role(relative: Path) -> str:
    if len(relative.parts) > 1 and relative.parts[0] == "original":
        return "original"
    if len(relative.parts) > 1 and relative.parts[0] == "assets":
        return "asset"
    if relative.as_posix() == "content.md":
        return "normalized"
    return "derivative"


def regular_file_without_links(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1


def read_json_object(path: Path, reporter: Reporter, label: str) -> dict[str, object] | None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        reporter.error(path, f"无法读取 {label}：{exc}")
        return None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        reporter.error(path, f"{label} 必须是普通文件且不能是符号链接")
        return None
    if metadata.st_nlink > 1:
        reporter.error(path, f"{label} 禁止硬链接")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        reporter.error(path, f"{label} 不是有效 JSON：{exc}")
        return None
    if not isinstance(data, dict):
        reporter.error(path, f"{label} 根节点必须是对象")
        return None
    return data


def validate_state_and_rule(vault: Path, reporter: Reporter) -> None:
    state_path = vault / ".digital-brain/state.json"
    state = read_json_object(state_path, reporter, "state.json")
    if state is None:
        return
    if state_path.stat().st_mode & 0o222:
        reporter.warning(state_path, "state.json 仍有写权限")
    if state.get("version") != 1:
        reporter.error(state_path, "不支持的 state version")
    rule_name = state.get("rule_file")
    expected_hash = state.get("schema_sha256")
    if not isinstance(rule_name, str):
        reporter.error(state_path, "rule_file 必须是字符串")
        return
    rule_relative = Path(rule_name)
    if (
        rule_relative.is_absolute()
        or rule_relative.name != rule_name
        or rule_relative.suffix.lower() != ".md"
        or rule_name.casefold() in {"index.md", "log.md"}
    ):
        reporter.error(state_path, "rule_file 必须是 vault 根目录下的独立 .md 文件")
        return
    rule_path = vault / rule_name
    if not regular_file_without_links(rule_path):
        reporter.error(rule_path, "规则文件必须是普通文件，且不能是 symlink 或 hardlink")
        return
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        reporter.error(state_path, "schema_sha256 格式无效")
        return
    if sha256_file(rule_path) != expected_hash:
        reporter.error(rule_path, "规则文件与初始化时的 Schema 校验值不一致")


def load_registered_buckets(vault: Path, reporter: Reporter) -> set[str] | None:
    config_path = vault / ".digital-brain/config.json"
    config = read_json_object(config_path, reporter, "config.json")
    if config is None:
        return None
    if config.get("version") != 1:
        reporter.error(config_path, "不支持的 config version")
    buckets = config.get("source_buckets")
    if not isinstance(buckets, list) or not buckets:
        reporter.error(config_path, "source_buckets 必须是非空数组")
        return None
    if any(
        not isinstance(bucket, str)
        or not NAME_PATTERN.fullmatch(bucket)
        or len(bucket) > 64
        for bucket in buckets
    ):
        reporter.error(config_path, "bucket 必须使用小写 kebab-case")
        return None
    if len(set(buckets)) != len(buckets):
        reporter.error(config_path, "source_buckets 不能重复")
        return None

    language = config.get("language")
    if not isinstance(language, str) or not language.strip():
        reporter.error(config_path, "language 必须是非空字符串")
    profile = config.get("profile")
    if not isinstance(profile, str):
        reporter.error(config_path, "profile 必须是 wiki/ 下的 Markdown 相对路径")
    else:
        profile_path = Path(profile)
        if (
            profile_path.is_absolute()
            or ".." in profile_path.parts
            or not profile_path.parts
            or profile_path.parts[0] != "wiki"
            or profile_path.suffix.lower() != ".md"
        ):
            reporter.error(config_path, "profile 必须是 wiki/ 下的 Markdown 相对路径")

    communication = config.get("communication")
    if not isinstance(communication, dict) or any(
        not isinstance(communication.get(key), str) or not communication.get(key, "").strip()
        for key in ("style", "detail")
    ):
        reporter.error(config_path, "communication.style/detail 必须是非空字符串")

    taxonomy = config.get("taxonomy")
    if not isinstance(taxonomy, dict):
        reporter.error(config_path, "taxonomy 必须是对象")
    else:
        all_tags: list[str] = []
        for category, tags in taxonomy.items():
            if not isinstance(category, str) or not isinstance(tags, list):
                reporter.error(config_path, "taxonomy 的分类名必须是字符串，值必须是数组")
                continue
            if any(
                not isinstance(tag, str)
                or not NAME_PATTERN.fullmatch(tag)
                or len(tag) > 64
                for tag in tags
            ):
                reporter.error(config_path, f"taxonomy.{category} 含无效 kebab-case 标签")
                continue
            all_tags.extend(tags)
        if len(set(all_tags)) != len(all_tags):
            reporter.error(config_path, "taxonomy 标签不能跨分类重复")

    ingestion = config.get("ingestion")
    if not isinstance(ingestion, dict) or not isinstance(ingestion.get("preferences"), dict):
        reporter.error(config_path, "ingestion.preferences 必须是对象")

    wiki = config.get("wiki")
    candidate = wiki.get("split_candidate_lines") if isinstance(wiki, dict) else None
    required = wiki.get("split_required_lines") if isinstance(wiki, dict) else None
    if (
        not isinstance(candidate, int)
        or isinstance(candidate, bool)
        or not isinstance(required, int)
        or isinstance(required, bool)
        or candidate <= 0
        or required <= candidate
    ):
        reporter.error(config_path, "wiki 拆分阈值必须是正整数，且 required 大于 candidate")

    privacy = config.get("privacy")
    if not isinstance(privacy, dict) or not isinstance(
        privacy.get("allow_external_processing"), bool
    ):
        reporter.error(config_path, "privacy.allow_external_processing 必须是布尔值")
    return set(buckets)


def scan_managed_tree(root: Path, reporter: Reporter) -> None:
    try:
        root_metadata = root.lstat()
    except OSError:
        return
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        return
    for current, dir_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(dir_names):
            path = current_path / name
            metadata = path.lstat()
            if contains_control_characters(name):
                reporter.error(path, "目录名禁止控制字符")
            if stat.S_ISLNK(metadata.st_mode):
                reporter.error(path, "受管目录中禁止符号链接")
                dir_names.remove(name)
            elif not stat.S_ISDIR(metadata.st_mode):
                reporter.error(path, "受管目录中禁止特殊目录项")
                dir_names.remove(name)
        for name in file_names:
            path = current_path / name
            metadata = path.lstat()
            if contains_control_characters(name):
                reporter.error(path, "文件名禁止控制字符")
            if stat.S_ISLNK(metadata.st_mode):
                reporter.error(path, "受管目录中禁止符号链接")
            elif not stat.S_ISREG(metadata.st_mode):
                reporter.error(path, "受管目录中禁止 FIFO、device 或 socket")
            elif metadata.st_nlink > 1:
                reporter.error(path, "受管目录中禁止硬链接")


def scan_snapshot_files(snapshot: Path, reporter: Reporter) -> set[str]:
    actual: set[str] = set()
    for current, dir_names, file_names in os.walk(snapshot, followlinks=False):
        current_path = Path(current)
        for name in list(dir_names):
            path = current_path / name
            metadata = path.lstat()
            if contains_control_characters(name):
                reporter.error(path, "快照目录名禁止控制字符")
            if stat.S_ISLNK(metadata.st_mode):
                reporter.error(path, "快照禁止符号链接目录")
                dir_names.remove(name)
            elif not stat.S_ISDIR(metadata.st_mode):
                reporter.error(path, "快照禁止特殊目录项")
                dir_names.remove(name)
        for name in file_names:
            path = current_path / name
            metadata = path.lstat()
            if contains_control_characters(name):
                reporter.error(path, "快照文件名禁止控制字符")
            if stat.S_ISLNK(metadata.st_mode):
                reporter.error(path, "快照禁止符号链接文件")
            elif not stat.S_ISREG(metadata.st_mode):
                reporter.error(path, "快照禁止 FIFO、device 或 socket")
            elif metadata.st_nlink > 1:
                reporter.error(path, "快照禁止硬链接文件")
            elif path.name != "manifest.json" or path.parent != snapshot:
                actual.add(path.relative_to(snapshot).as_posix())
    return actual


def validate_manifest(
    snapshot: Path, bucket: str, reporter: Reporter
) -> dict[str, object] | None:
    manifest_path = snapshot / "manifest.json"
    manifest = read_json_object(manifest_path, reporter, "manifest.json")
    actual_files = scan_snapshot_files(snapshot, reporter)
    if manifest is None:
        return None

    required = {
        "schema_version",
        "snapshot_id",
        "created_at",
        "bucket",
        "source",
        "content_digest",
        "files",
    }
    missing = sorted(required - manifest.keys())
    if missing:
        reporter.error(manifest_path, f"缺少字段：{', '.join(missing)}")
    if manifest.get("schema_version") != 1:
        reporter.error(manifest_path, "不支持的 schema_version")
    if manifest.get("snapshot_id") != snapshot.name:
        reporter.error(manifest_path, "snapshot_id 与目录名不一致")
    if manifest.get("bucket") != bucket:
        reporter.error(manifest_path, "bucket 与父目录名不一致")
    created_at = manifest.get("created_at")
    if not isinstance(created_at, str):
        reporter.error(manifest_path, "created_at 必须是字符串")
    else:
        try:
            timestamp = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("缺少时区")
        except ValueError:
            reporter.error(manifest_path, "created_at 必须是带时区的 ISO 8601 时间")

    source = manifest.get("source")
    if not isinstance(source, dict):
        reporter.error(manifest_path, "source 必须是对象")
    else:
        kind = source.get("kind")
        locator = source.get("locator")
        supersedes = source.get("supersedes")
        if kind not in SOURCE_KINDS:
            reporter.error(manifest_path, "source.kind 无效")
        if not isinstance(locator, str):
            reporter.error(manifest_path, "source.locator 必须是字符串")
        elif kind != "manual" and not locator:
            reporter.error(manifest_path, "非 manual 来源必须有稳定 locator")
        if supersedes is not None and not isinstance(supersedes, str):
            reporter.error(manifest_path, "source.supersedes 必须是字符串或 null")

    file_entries = manifest.get("files")
    if not isinstance(file_entries, list) or not file_entries:
        reporter.error(manifest_path, "files 必须是非空数组")
        return manifest

    registered: set[str] = set()
    validated_entries: list[dict[str, object]] = []
    entries_valid = True
    for index, entry in enumerate(file_entries):
        label = f"files[{index}]"
        if not isinstance(entry, dict) or not {"path", "role", "size", "sha256"}.issubset(entry):
            reporter.error(manifest_path, f"{label} 必须是字段完整的对象")
            entries_valid = False
            continue
        relative_text = entry.get("path")
        if not isinstance(relative_text, str):
            reporter.error(manifest_path, f"{label}.path 必须是字符串")
            entries_valid = False
            continue
        relative = Path(relative_text)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative_text in registered
            or contains_control_characters(relative_text)
        ):
            reporter.error(manifest_path, f"{label}.path 非法或重复：{relative_text}")
            entries_valid = False
            continue
        if entry.get("role") not in FILE_ROLES:
            reporter.error(manifest_path, f"{label}.role 无效")
            entries_valid = False
        elif entry.get("role") != expected_role(relative):
            reporter.error(manifest_path, f"{label}.role 与文件路径不一致")
            entries_valid = False
        registered.add(relative_text)
        path = snapshot / relative
        resolved = path.resolve(strict=False)
        if not is_relative_to(resolved, snapshot.resolve()):
            reporter.error(path, "manifest 路径越界")
            entries_valid = False
            continue
        try:
            metadata = path.lstat()
        except OSError:
            reporter.error(path, "manifest 登记文件不存在")
            entries_valid = False
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink > 1:
            reporter.error(path, "manifest 登记项不是独立普通文件")
            entries_valid = False
            continue
        actual_size = metadata.st_size
        actual_hash = sha256_file(path)
        if entry.get("size") != actual_size:
            reporter.error(path, "文件大小与 manifest 不一致")
            entries_valid = False
        if entry.get("sha256") != actual_hash:
            reporter.error(path, "sha256 与 manifest 不一致，raw 可能已被修改")
            entries_valid = False
        if metadata.st_mode & 0o222:
            reporter.warning(path, "快照文件仍有写权限")
        validated_entries.append(
            {
                "path": relative_text,
                "role": entry.get("role"),
                "size": actual_size,
                "sha256": actual_hash,
            }
        )

    for extra in sorted(actual_files - registered):
        reporter.error(snapshot / extra, "文件未登记在 manifest 中")
        entries_valid = False
    for absent in sorted(registered - actual_files):
        reporter.error(snapshot / absent, "manifest 登记文件不存在")
        entries_valid = False

    if entries_valid and len(validated_entries) == len(file_entries):
        digest = calculate_content_digest(validated_entries)
        if manifest.get("content_digest") != digest:
            reporter.error(manifest_path, "content_digest 与文件清单不一致")
    if isinstance(source, dict) and source.get("kind") == "file":
        if not any(entry.get("role") == "original" for entry in file_entries if isinstance(entry, dict)):
            reporter.error(manifest_path, "file 来源必须保留 original 原件")
    if manifest_path.stat().st_mode & 0o222:
        reporter.warning(manifest_path, "manifest 仍有写权限")
    if snapshot.stat().st_mode & 0o222:
        reporter.warning(snapshot, "snapshot 目录仍有写权限")
    return manifest


def validate_supersedes_reference(
    vault: Path,
    manifest_path: Path,
    manifest: dict[str, object],
    reporter: Reporter,
) -> None:
    source = manifest.get("source")
    if not isinstance(source, dict) or source.get("supersedes") is None:
        return
    value = source.get("supersedes")
    if not isinstance(value, str):
        return
    if source.get("kind") == "manual" and not source.get("locator"):
        reporter.error(manifest_path, "空 locator 的 manual 来源不能使用 supersedes")
        return
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or contains_control_characters(value):
        reporter.error(manifest_path, "source.supersedes 必须是 vault 内相对路径")
        return
    target = vault / relative
    resolved = target.resolve(strict=False)
    if not is_relative_to(resolved, (vault / "raw").resolve()) or target.name != "manifest.json":
        reporter.error(manifest_path, "source.supersedes 必须指向 raw/ 下的 manifest.json")
        return
    if resolved == manifest_path.resolve():
        reporter.error(manifest_path, "source.supersedes 不能指向自身")
        return
    target_manifest = read_json_object(target, reporter, "被替代的 manifest.json")
    if target_manifest is None:
        reporter.error(manifest_path, "source.supersedes 指向无效 manifest")
        return
    target_source = target_manifest.get("source")
    if not isinstance(target_source, dict) or (
        target_source.get("kind") != source.get("kind")
        or target_source.get("locator") != source.get("locator")
    ):
        reporter.error(manifest_path, "source.supersedes 必须指向同一来源")


def validate_source_chains(
    vault: Path,
    manifests: list[tuple[Path, dict[str, object]]],
    reporter: Reporter,
) -> None:
    groups: dict[tuple[str, str], list[tuple[Path, dict[str, object]]]] = defaultdict(list)
    for manifest_path, manifest in manifests:
        validate_supersedes_reference(vault, manifest_path, manifest, reporter)
        source = manifest.get("source")
        if not isinstance(source, dict):
            continue
        kind = source.get("kind")
        locator = source.get("locator")
        if isinstance(kind, str) and isinstance(locator, str) and locator:
            groups[(kind, locator)].append((manifest_path, manifest))

    for versions in groups.values():
        by_reference = {
            path.relative_to(vault).as_posix(): (path, manifest)
            for path, manifest in versions
        }
        roots: list[str] = []
        children: dict[str, str] = {}
        for reference, (manifest_path, manifest) in by_reference.items():
            source = manifest.get("source")
            if not isinstance(source, dict):
                continue
            parent = source.get("supersedes")
            if parent is None:
                roots.append(reference)
            elif not isinstance(parent, str) or parent not in by_reference:
                reporter.error(
                    manifest_path,
                    f"source.supersedes 链不连续：{parent!r}",
                )
            elif parent in children:
                reporter.error(manifest_path, f"source.supersedes 链出现分叉：{parent}")
            else:
                children[parent] = reference

        if len(roots) != 1:
            for manifest_path, _ in versions:
                reporter.error(manifest_path, "同一来源必须且只能有一个链起点")
            continue
        current = roots[0]
        visited: set[str] = set()
        previous_manifest: dict[str, object] | None = None
        while current in by_reference and current not in visited:
            visited.add(current)
            manifest_path, manifest = by_reference[current]
            if previous_manifest and manifest.get("content_digest") == previous_manifest.get(
                "content_digest"
            ):
                reporter.warning(manifest_path, "同一来源出现内容完全相同的重复快照")
            previous_manifest = manifest
            child = children.get(current)
            if child is None:
                break
            current = child
        if len(visited) != len(by_reference):
            for reference, (manifest_path, _) in by_reference.items():
                if reference not in visited:
                    reporter.error(manifest_path, "source.supersedes 链存在循环或孤立版本")


def validate_raw(vault: Path, buckets: set[str] | None, reporter: Reporter) -> int:
    raw = vault / "raw"
    try:
        raw_metadata = raw.lstat()
    except OSError:
        return 0
    if stat.S_ISLNK(raw_metadata.st_mode) or not stat.S_ISDIR(raw_metadata.st_mode):
        return 0

    count = 0
    manifests: list[tuple[Path, dict[str, object]]] = []
    for bucket in sorted(raw.iterdir()):
        metadata = bucket.lstat()
        if contains_control_characters(bucket.name):
            reporter.error(bucket, "bucket 名禁止控制字符")
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            reporter.error(bucket, "raw/ 下只允许非链接 bucket 目录")
            continue
        if buckets is not None and bucket.name not in buckets:
            reporter.error(bucket, "bucket 未在 config.json 注册")
        for snapshot in sorted(bucket.iterdir()):
            snapshot_metadata = snapshot.lstat()
            if contains_control_characters(snapshot.name):
                reporter.error(snapshot, "snapshot 目录名禁止控制字符")
            if stat.S_ISLNK(snapshot_metadata.st_mode) or not stat.S_ISDIR(snapshot_metadata.st_mode):
                reporter.error(snapshot, "bucket 下只允许非链接 snapshot 目录")
                continue
            count += 1
            manifest = validate_manifest(snapshot, bucket.name, reporter)
            if manifest is not None:
                manifests.append((snapshot / "manifest.json", manifest))
    validate_source_chains(vault, manifests, reporter)
    return count


def validate_staging(vault: Path, reporter: Reporter) -> None:
    staging = vault / ".staging"
    try:
        metadata = staging.lstat()
    except OSError:
        return
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        return
    scan_managed_tree(staging, reporter)
    leftovers = list(staging.iterdir())
    if leftovers:
        reporter.warning(staging, f"存在 {len(leftovers)} 个未完成的暂存任务")


def validate_structure(vault: Path, reporter: Reporter) -> None:
    for relative in REQUIRED_DIRECTORIES:
        path = vault / relative
        try:
            metadata = path.lstat()
        except OSError:
            reporter.error(path, "缺少目录")
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            reporter.error(path, "目录类型无效或是符号链接")
    for relative in REQUIRED_FILES:
        path = vault / relative
        if not regular_file_without_links(path):
            reporter.error(path, "缺少独立普通文件，或文件是 symlink/hardlink")
    gitignore = vault / ".gitignore"
    if regular_file_without_links(gitignore):
        lines = {line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()}
        if ".staging/" not in lines:
            reporter.error(gitignore, "必须忽略 .staging/")


def main() -> int:
    args = parse_args()
    try:
        vault = args.vault.expanduser().resolve(strict=True)
    except OSError as exc:
        print(f"验证失败：{exc}", file=sys.stderr)
        return 2
    if not vault.is_dir():
        print(f"验证失败：vault 不是目录：{vault}", file=sys.stderr)
        return 2

    reporter = Reporter()
    validate_structure(vault, reporter)
    validate_state_and_rule(vault, reporter)
    buckets = load_registered_buckets(vault, reporter)
    snapshot_count = validate_raw(vault, buckets, reporter)
    validate_staging(vault, reporter)

    wiki = vault / "wiki"
    try:
        wiki_metadata = wiki.lstat()
    except OSError:
        wiki_metadata = None
    if wiki_metadata and stat.S_ISDIR(wiki_metadata.st_mode) and not stat.S_ISLNK(
        wiki_metadata.st_mode
    ):
        scan_managed_tree(wiki, reporter)

    for issue in reporter.errors:
        print(f"[ERROR] {issue}")
    for issue in reporter.warnings:
        print(f"[WARNING] {issue}")
    print(
        f"检查完成：{snapshot_count} 个 snapshot，"
        f"{len(reporter.errors)} 个错误，{len(reporter.warnings)} 个警告。"
    )
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
