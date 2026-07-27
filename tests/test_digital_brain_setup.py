from __future__ import annotations

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


def unlock_and_remove(path: Path) -> None:
    """清理测试目录，并兼容旧版本可能留下的只读文件。"""
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

    def run_init(
        self,
        target: Path,
        *args: object,
        script: Path = INIT,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), str(target), *(str(arg) for arg in args)],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.temp_root,
        )

    def assert_initialized(self, vault: Path, rule_file: str) -> None:
        expected_names = {
            rule_file,
            "START-HERE.md",
            "profile.md",
            "index.md",
            "inbox",
            "raw",
            "wiki",
        }
        self.assertEqual({path.name for path in vault.iterdir()}, expected_names)
        self.assertTrue((vault / rule_file).is_file())
        self.assertTrue((vault / "START-HERE.md").is_file())
        self.assertTrue((vault / "profile.md").is_file())
        self.assertTrue((vault / "index.md").is_file())
        for directory in ("inbox", "raw", "wiki"):
            self.assertTrue((vault / directory).is_dir())
            self.assertEqual(list((vault / directory).iterdir()), [])

    def test_initializes_small_codex_vault_without_runtime_state(self) -> None:
        vault = self.temp_root / "codex-vault"
        result = self.run_init(vault, "--agent", "codex")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_initialized(vault, "AGENTS.md")
        self.assertEqual(
            (vault / "AGENTS.md").read_bytes(),
            (SKILL / "assets/Schema.md").read_bytes(),
        )
        self.assertFalse((vault / ".digital-brain").exists())
        forbidden_names = {"manifest.json", "state.json", "log.md"}
        self.assertFalse(
            any(path.name in forbidden_names for path in vault.rglob("*"))
        )

    def test_uses_agent_specific_rule_file(self) -> None:
        expected = {
            "claude": "CLAUDE.md",
            "gemini": "GEMINI.md",
        }
        for agent, rule_file in expected.items():
            with self.subTest(agent=agent):
                vault = self.temp_root / f"{agent}-vault"
                result = self.run_init(vault, "--agent", agent)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_initialized(vault, rule_file)
                self.assertFalse((vault / "AGENTS.md").exists())

    def test_supports_safe_custom_rule_file(self) -> None:
        vault = self.temp_root / "custom-vault"
        result = self.run_init(
            vault,
            "--agent",
            "other",
            "--rule-file",
            "MY-BRAIN.md",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_initialized(vault, "MY-BRAIN.md")
        self.assertEqual(
            (vault / "MY-BRAIN.md").read_bytes(),
            (SKILL / "assets/Schema.md").read_bytes(),
        )

    def test_rejects_unsafe_custom_rule_file(self) -> None:
        absolute_rule = self.temp_root / "absolute-rule.md"
        cases = (
            "../escaped-rule.md",
            "nested/RULES.md",
            str(absolute_rule),
            "RULES.txt",
            "index.md",
            "INDEX.md",
            "profile.md",
            "START-HERE.md",
        )
        for index, rule_file in enumerate(cases):
            with self.subTest(rule_file=rule_file):
                vault = self.temp_root / f"unsafe-{index}"
                result = self.run_init(
                    vault,
                    "--agent",
                    "other",
                    "--rule-file",
                    rule_file,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(vault.exists())

        self.assertFalse((self.temp_root / "escaped-rule.md").exists())
        self.assertFalse(absolute_rule.exists())

    def test_enforces_custom_rule_file_cli_contract(self) -> None:
        missing = self.run_init(
            self.temp_root / "missing-rule",
            "--agent",
            "other",
        )
        unexpected = self.run_init(
            self.temp_root / "unexpected-rule",
            "--agent",
            "codex",
            "--rule-file",
            "CUSTOM.md",
        )

        self.assertNotEqual(missing.returncode, 0)
        self.assertNotEqual(unexpected.returncode, 0)
        self.assertFalse((self.temp_root / "missing-rule").exists())
        self.assertFalse((self.temp_root / "unexpected-rule").exists())

    def test_refuses_non_empty_target_without_overwriting(self) -> None:
        vault = self.temp_root / "occupied"
        vault.mkdir()
        marker = vault / "keep.txt"
        marker.write_text("不能覆盖\n", encoding="utf-8")

        result = self.run_init(vault, "--agent", "codex")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(encoding="utf-8"), "不能覆盖\n")
        self.assertEqual(list(vault.iterdir()), [marker])

    def test_refuses_symlink_target_without_touching_destination(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("当前平台不支持符号链接")
        destination = self.temp_root / "destination"
        destination.mkdir()
        target = self.temp_root / "linked-vault"
        target.symlink_to(destination, target_is_directory=True)

        result = self.run_init(target, "--agent", "codex")

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(target.is_symlink())
        self.assertEqual(list(destination.iterdir()), [])

    def test_isolated_skill_copy_remains_self_contained(self) -> None:
        self.assertEqual(
            (SKILL / "LICENSE").read_bytes(),
            (ROOT / "LICENSE").read_bytes(),
        )
        distribution = self.temp_root / "distribution"
        copied_skill = distribution / "digital-brain-setup"
        shutil.copytree(SKILL, copied_skill)
        vault = self.temp_root / "isolated-vault"

        result = self.run_init(
            vault,
            "--agent",
            "claude",
            script=copied_skill / "scripts/init_vault.py",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_initialized(vault, "CLAUDE.md")
        self.assertFalse((vault / ".digital-brain").exists())

    def test_skill_trigger_and_first_ingestion_contract(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("不要因查询、整理或维护已有知识库而触发", skill_text)
        self.assertIn("现在要提供第一份资料", skill_text)
        self.assertIn("还是稍后再开始", skill_text)


if __name__ == "__main__":
    unittest.main()
