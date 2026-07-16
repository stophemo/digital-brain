from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "digital-brain-setup"
INIT = SKILL / "scripts/init_vault.py"
FINALIZE = SKILL / "scripts/finalize_snapshot.py"


def unlock_and_remove(path: Path) -> None:
    if not path.exists():
        return
    for current, dir_names, file_names in os.walk(path, topdown=False):
        current_path = Path(current)
        for name in file_names:
            (current_path / name).chmod(0o600)
        for name in dir_names:
            (current_path / name).chmod(0o700)
        current_path.chmod(0o700)
    shutil.rmtree(path)


class DigitalBrainSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="digital-brain-test-"))
        self.addCleanup(unlock_and_remove, self.temp_root)

    def run_script(self, script: Path, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *(str(arg) for arg in args)],
            check=False,
            capture_output=True,
            text=True,
        )

    def initialize(self, name: str = "vault") -> Path:
        vault = self.temp_root / name
        result = self.run_script(INIT, vault, "--agent", "codex")
        self.assertEqual(result.returncode, 0, result.stderr)
        return vault

    def stage_text_source(self, vault: Path, task: str = "task") -> Path:
        staging = vault / ".staging" / task
        (staging / "original").mkdir(parents=True)
        (staging / "original/source.txt").write_text("原始内容\n", encoding="utf-8")
        (staging / "content.md").write_text("# 标准化内容\n", encoding="utf-8")
        return staging

    def finalize(
        self,
        vault: Path,
        staging: Path,
        *,
        bucket: str = "general",
        locator: str = "source:test",
        source_kind: str = "file",
        supersedes: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        arguments: list[object] = [
            "--vault",
            vault,
            "--staging",
            staging,
            "--bucket",
            bucket,
            "--slug",
            "example",
            "--source-kind",
            source_kind,
            "--source-locator",
            locator,
        ]
        if supersedes:
            arguments.extend(("--supersedes", supersedes))
        return self.run_script(FINALIZE, *arguments)

    def test_initializes_and_validates_empty_vault(self) -> None:
        vault = self.initialize()
        self.assertEqual(
            (vault / "AGENTS.md").read_bytes(),
            (SKILL / "assets/Schema.md").read_bytes(),
        )
        validator = vault / ".digital-brain/scripts/validate_vault.py"
        result = self.run_script(validator, vault)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 个错误", result.stdout)

    def test_refuses_non_empty_target_without_overwriting(self) -> None:
        vault = self.temp_root / "occupied"
        vault.mkdir()
        marker = vault / "keep.txt"
        marker.write_text("不能覆盖", encoding="utf-8")
        result = self.run_script(INIT, vault, "--agent", "codex")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(encoding="utf-8"), "不能覆盖")
        self.assertFalse((vault / "AGENTS.md").exists())

    def test_requires_explicit_gate_inside_git_worktree_with_remote(self) -> None:
        repo = self.temp_root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(repo), "remote", "add", "origin", "https://example.invalid/repo.git"],
            check=True,
            capture_output=True,
        )
        vault = repo / "vault"
        refused = self.run_script(INIT, vault, "--agent", "codex")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--allow-existing-git", refused.stderr)
        allowed = self.run_script(
            INIT, vault, "--agent", "codex", "--allow-existing-git"
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_isolated_skill_copy_remains_self_contained(self) -> None:
        distribution = self.temp_root / "distribution"
        copied_skill = distribution / "digital-brain-setup"
        shutil.copytree(SKILL, copied_skill)
        vault = self.temp_root / "isolated-vault"
        result = self.run_script(
            copied_skill / "scripts/init_vault.py", vault, "--agent", "claude"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((vault / "CLAUDE.md").is_file())
        self.assertFalse((vault / "AGENTS.md").exists())

    def test_finalizes_snapshot_and_detects_tampering(self) -> None:
        vault = self.initialize()
        staging = self.stage_text_source(vault)
        result = self.finalize(vault, staging)
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshots = list((vault / "raw/general").iterdir())
        self.assertEqual(len(snapshots), 1)
        snapshot = snapshots[0]
        manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["snapshot_id"], snapshot.name)
        self.assertEqual({item["role"] for item in manifest["files"]}, {"original", "normalized"})
        self.assertFalse(staging.exists())

        validator = vault / ".digital-brain/scripts/validate_vault.py"
        valid = self.run_script(validator, vault)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

        content = snapshot / "content.md"
        content.chmod(0o600)
        content.write_text("已被篡改\n", encoding="utf-8")
        invalid = self.run_script(validator, vault)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("sha256 与 manifest 不一致", invalid.stdout)

    def test_duplicate_source_reuses_existing_snapshot(self) -> None:
        vault = self.initialize()
        first = self.stage_text_source(vault, "first")
        self.assertEqual(self.finalize(vault, first).returncode, 0)
        second = self.stage_text_source(vault, "second")
        duplicate = self.finalize(vault, second)
        self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
        self.assertIn("复用已有快照", duplicate.stdout)
        self.assertTrue(second.exists())
        self.assertEqual(len(list((vault / "raw/general").iterdir())), 1)

    def test_rejects_symlink_in_staging(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("当前平台不支持符号链接")
        vault = self.initialize()
        staging = vault / ".staging/task"
        (staging / "original").mkdir(parents=True)
        outside = self.temp_root / "outside.txt"
        outside.write_text("外部内容", encoding="utf-8")
        os.symlink(outside, staging / "original/link.txt")
        result = self.finalize(vault, staging)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("禁止符号链接", result.stderr)
        self.assertFalse((vault / "raw/general").exists())

    def test_rejects_symlinked_raw_root(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("当前平台不支持符号链接")
        vault = self.initialize()
        staging = self.stage_text_source(vault)
        raw = vault / "raw"
        raw.rmdir()
        outside_raw = self.temp_root / "outside-raw"
        outside_raw.mkdir()
        os.symlink(outside_raw, raw)
        result = self.finalize(vault, staging)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("禁止是符号链接", result.stderr)
        self.assertEqual(list(outside_raw.iterdir()), [])

        validator = vault / ".digital-brain/scripts/validate_vault.py"
        validation = self.run_script(validator, vault)
        self.assertEqual(validation.returncode, 1)
        self.assertIn("目录类型无效或是符号链接", validation.stdout)

    def test_validator_rejects_symlinked_or_modified_rule_file(self) -> None:
        vault = self.initialize()
        validator = vault / ".digital-brain/scripts/validate_vault.py"
        recorder = vault / ".digital-brain/scripts/record_schema_update.py"
        rule = vault / "AGENTS.md"
        rule.write_text("# 被修改的规则\n", encoding="utf-8")
        modified = self.run_script(validator, vault)
        self.assertEqual(modified.returncode, 1)
        self.assertIn("Schema 校验值不一致", modified.stdout)

        accepted = self.run_script(recorder, vault)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        valid_again = self.run_script(validator, vault)
        self.assertEqual(valid_again.returncode, 0, valid_again.stdout + valid_again.stderr)

        rule.unlink()
        outside = self.temp_root / "outside-rule.md"
        outside.write_text("外部文件", encoding="utf-8")
        os.symlink(outside, rule)
        linked = self.run_script(validator, vault)
        self.assertEqual(linked.returncode, 1)
        self.assertIn("symlink", linked.stdout)

    def test_validator_rejects_manifest_symlink_and_fifo(self) -> None:
        if not hasattr(os, "symlink") or not hasattr(os, "mkfifo"):
            self.skipTest("当前平台不支持符号链接或 FIFO")
        vault = self.initialize()
        snapshot = vault / "raw/general/fake-snapshot"
        snapshot.mkdir(parents=True)
        outside_manifest = self.temp_root / "outside-manifest.json"
        outside_manifest.write_text("{}\n", encoding="utf-8")
        os.symlink(outside_manifest, snapshot / "manifest.json")
        os.mkfifo(snapshot / "unregistered.pipe")

        validator = vault / ".digital-brain/scripts/validate_vault.py"
        result = self.run_script(validator, vault)
        self.assertEqual(result.returncode, 1)
        self.assertIn("manifest.json 必须是普通文件", result.stdout)
        self.assertIn("FIFO", result.stdout)

    def test_enforces_registered_bucket_during_freeze_and_validation(self) -> None:
        vault = self.initialize()
        staging = self.stage_text_source(vault)
        refused = self.finalize(vault, staging, bucket="unregistered")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("bucket 未在 config.json 注册", refused.stderr)

        accepted = self.finalize(vault, staging)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        config_path = vault / ".digital-brain/config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["source_buckets"] = ["other"]
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        validator = vault / ".digital-brain/scripts/validate_vault.py"
        validation = self.run_script(validator, vault)
        self.assertEqual(validation.returncode, 1)
        self.assertIn("bucket 未在 config.json 注册", validation.stdout)

    def test_changed_source_requires_continuous_supersedes_chain(self) -> None:
        vault = self.initialize()
        first = self.stage_text_source(vault, "first-version")
        self.assertEqual(self.finalize(vault, first).returncode, 0)
        previous = next((vault / "raw/general").iterdir()) / "manifest.json"
        previous_ref = previous.relative_to(vault).as_posix()

        second = self.stage_text_source(vault, "second-version")
        (second / "original/source.txt").write_text("更新后的原始内容\n", encoding="utf-8")
        (second / "content.md").write_text("# 更新后的标准化内容\n", encoding="utf-8")
        missing_link = self.finalize(vault, second)
        self.assertEqual(missing_link.returncode, 1)
        self.assertIn("必须使用 --supersedes", missing_link.stderr)

        linked = self.finalize(vault, second, supersedes=previous_ref)
        self.assertEqual(linked.returncode, 0, linked.stderr)
        validator = vault / ".digital-brain/scripts/validate_vault.py"
        validation = self.run_script(validator, vault)
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

        manifests = list((vault / "raw/general").glob("*/manifest.json"))
        root_manifest = next(
            path
            for path in manifests
            if json.loads(path.read_text(encoding="utf-8"))["source"]["supersedes"] is None
        )
        child_manifest = next(path for path in manifests if path != root_manifest)
        for path, timestamp in (
            (root_manifest, "2099-01-01T00:00:00.000000Z"),
            (child_manifest, "2000-01-01T00:00:00.000000Z"),
        ):
            path.chmod(0o600)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["created_at"] = timestamp
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            path.chmod(0o400)
        clock_rollback = self.run_script(validator, vault)
        self.assertEqual(
            clock_rollback.returncode, 0, clock_rollback.stdout + clock_rollback.stderr
        )

    def test_rejects_control_characters_and_hardlinks(self) -> None:
        vault = self.initialize()
        control = self.stage_text_source(vault, "control")
        (control / "bad\nname.txt").write_text("非法文件名", encoding="utf-8")
        refused_control = self.finalize(vault, control)
        self.assertEqual(refused_control.returncode, 1)
        self.assertIn("控制字符", refused_control.stderr)

        if hasattr(os, "link"):
            hardlink = self.stage_text_source(vault, "hardlink")
            os.link(hardlink / "content.md", hardlink / "duplicate.md")
            refused_link = self.finalize(vault, hardlink)
            self.assertEqual(refused_link.returncode, 1)
            self.assertIn("硬链接", refused_link.stderr)

    def test_other_agent_rule_name_is_case_insensitively_safe(self) -> None:
        vault = self.temp_root / "custom-rule"
        result = self.run_script(
            INIT,
            vault,
            "--agent",
            "other",
            "--rule-file",
            "INDEX.md",
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(vault.exists())

    def test_reverted_content_creates_a_new_version_event(self) -> None:
        vault = self.initialize()
        first = self.stage_text_source(vault, "version-a")
        self.assertEqual(self.finalize(vault, first).returncode, 0)
        first_snapshot = next((vault / "raw/general").iterdir())

        second = self.stage_text_source(vault, "version-b")
        (second / "original/source.txt").write_text("版本 B\n", encoding="utf-8")
        (second / "content.md").write_text("# 版本 B\n", encoding="utf-8")
        self.assertEqual(
            self.finalize(
                vault,
                second,
                supersedes=(first_snapshot / "manifest.json").relative_to(vault).as_posix(),
            ).returncode,
            0,
        )
        second_snapshot = next(
            path for path in (vault / "raw/general").iterdir() if path != first_snapshot
        )

        reverted = self.stage_text_source(vault, "version-a-again")
        result = self.finalize(
            vault,
            reverted,
            supersedes=(second_snapshot / "manifest.json").relative_to(vault).as_posix(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("复用已有快照", result.stdout)
        self.assertEqual(len(list((vault / "raw/general").iterdir())), 3)

    def test_validator_rejects_manual_self_cycle(self) -> None:
        vault = self.initialize()
        staging = vault / ".staging/manual"
        staging.mkdir(parents=True)
        (staging / "content.md").write_text("# 手工记录\n", encoding="utf-8")
        result = self.finalize(vault, staging, locator="", source_kind="manual")
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest_path = next((vault / "raw/general").glob("*/manifest.json"))
        manifest_path.chmod(0o600)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["source"]["supersedes"] = manifest_path.relative_to(vault).as_posix()
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest_path.chmod(0o400)
        validator = vault / ".digital-brain/scripts/validate_vault.py"
        validation = self.run_script(validator, vault)
        self.assertEqual(validation.returncode, 1)
        self.assertIn("空 locator", validation.stdout)

    def test_validator_rejects_invalid_config_types_and_paths(self) -> None:
        vault = self.initialize()
        config_path = vault / ".digital-brain/config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["privacy"]["allow_external_processing"] = "yes"
        config["wiki"]["split_required_lines"] = "never"
        config["profile"] = "../../outside.md"
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        validator = vault / ".digital-brain/scripts/validate_vault.py"
        validation = self.run_script(validator, vault)
        self.assertEqual(validation.returncode, 1)
        self.assertIn("allow_external_processing 必须是布尔值", validation.stdout)
        self.assertIn("profile 必须是 wiki/", validation.stdout)
        self.assertIn("拆分阈值必须是正整数", validation.stdout)

    def test_file_source_requires_real_original_directory(self) -> None:
        vault = self.initialize()
        staging = vault / ".staging/fake-original"
        staging.mkdir(parents=True)
        (staging / "original").write_text("这不是目录", encoding="utf-8")
        (staging / "content.md").write_text("# 内容\n", encoding="utf-8")
        result = self.finalize(vault, staging)
        self.assertEqual(result.returncode, 1)
        self.assertIn("original/ 目录", result.stderr)

    def test_validator_rejects_control_character_directory_in_raw(self) -> None:
        vault = self.initialize()
        staging = self.stage_text_source(vault)
        self.assertEqual(self.finalize(vault, staging).returncode, 0)
        snapshot = next((vault / "raw/general").iterdir())
        snapshot.chmod(0o700)
        bad_directory = snapshot / "bad\nname"
        bad_directory.mkdir()
        bad_directory.chmod(0o500)
        snapshot.chmod(0o500)
        validator = vault / ".digital-brain/scripts/validate_vault.py"
        validation = self.run_script(validator, vault)
        self.assertEqual(validation.returncode, 1)
        self.assertIn("控制字符", validation.stdout)


if __name__ == "__main__":
    unittest.main()
