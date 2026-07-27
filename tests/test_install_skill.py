from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "digital-brain-setup"
INSTALLER = ROOT / "scripts/install_skill.py"
IGNORED_PACKAGE_NAMES = {".DS_Store", "__pycache__"}


def snapshot_tree(
    root: Path,
    *,
    ignore_package_artifacts: bool = False,
) -> dict[str, tuple[str, bytes | str | None]]:
    """记录目录树类型和内容，用于验证发布包被完整复制。"""
    snapshot: dict[str, tuple[str, bytes | str | None]] = {}
    for path in root.rglob("*"):
        relative_path = path.relative_to(root)
        if ignore_package_artifacts and (
            any(part in IGNORED_PACKAGE_NAMES for part in relative_path.parts)
            or path.suffix == ".pyc"
        ):
            continue
        relative = relative_path.as_posix()
        if path.is_symlink():
            snapshot[relative] = ("symlink", os.readlink(path))
        elif path.is_dir():
            snapshot[relative] = ("directory", None)
        elif path.is_file():
            snapshot[relative] = ("file", path.read_bytes())
        else:
            snapshot[relative] = ("other", None)
    return snapshot


class InstallSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="digital-brain-install-test-"
        )
        self.addCleanup(temporary_directory.cleanup)
        self.temp_root = Path(temporary_directory.name)
        self.home = self.temp_root / "home"
        self.home.mkdir()

        self.base_env = os.environ.copy()
        self.base_env["HOME"] = str(self.home)
        self.base_env["USERPROFILE"] = str(self.home)
        self.base_env["PYTHONIOENCODING"] = "cp1252"
        self.base_env.pop("CODEX_HOME", None)
        self.base_env.pop("CLAUDE_CONFIG_DIR", None)

    def run_installer(
        self,
        client: str,
        *args: object,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                client,
                *(str(arg) for arg in args),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=self.temp_root,
            env=env or self.base_env,
        )

    def assert_complete_skill_copy(self, installed_skill: Path) -> None:
        self.assertTrue(installed_skill.is_dir())
        self.assertEqual(
            snapshot_tree(installed_skill),
            snapshot_tree(SKILL, ignore_package_artifacts=True),
        )

    def test_codex_uses_home_default_and_copies_complete_skill(self) -> None:
        result = self.run_installer("codex")

        installed_skill = (
            self.home / ".codex/skills/digital-brain-setup"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_complete_skill_copy(installed_skill)
        self.assertFalse((self.home / ".claude").exists())

    def test_claude_uses_home_default_and_copies_complete_skill(self) -> None:
        result = self.run_installer("claude")

        installed_skill = (
            self.home / ".claude/skills/digital-brain-setup"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_complete_skill_copy(installed_skill)
        self.assertFalse((self.home / ".codex").exists())

    def test_client_configuration_directory_environment_is_honored(self) -> None:
        cases = (
            ("codex", "CODEX_HOME"),
            ("claude", "CLAUDE_CONFIG_DIR"),
        )
        for client, variable in cases:
            with self.subTest(client=client):
                config_directory = self.temp_root / f"{client}-config"
                env = self.base_env.copy()
                env[variable] = str(config_directory)

                result = self.run_installer(client, env=env)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_complete_skill_copy(
                    config_directory / "skills/digital-brain-setup"
                )

    def test_empty_configuration_directory_uses_home_default(self) -> None:
        cases = (
            ("codex", "CODEX_HOME", self.home / ".codex"),
            ("claude", "CLAUDE_CONFIG_DIR", self.home / ".claude"),
        )
        for client, variable, default_root in cases:
            with self.subTest(client=client):
                env = self.base_env.copy()
                env[variable] = ""

                result = self.run_installer(client, env=env)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_complete_skill_copy(
                    default_root / "skills/digital-brain-setup"
                )

    def test_skills_dir_overrides_client_default(self) -> None:
        cases = ("codex", "claude")
        for client in cases:
            with self.subTest(client=client):
                skills_directory = self.temp_root / f"{client}-skills"
                env = self.base_env.copy()
                env["CODEX_HOME"] = str(self.temp_root / "unused-codex")
                env["CLAUDE_CONFIG_DIR"] = str(
                    self.temp_root / "unused-claude"
                )

                result = self.run_installer(
                    client,
                    "--skills-dir",
                    skills_directory,
                    env=env,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_complete_skill_copy(
                    skills_directory / "digital-brain-setup"
                )
                self.assertFalse((self.temp_root / "unused-codex").exists())
                self.assertFalse((self.temp_root / "unused-claude").exists())

    def test_reinstalling_identical_skill_is_idempotent(self) -> None:
        skills_directory = self.temp_root / "idempotent-skills"
        first = self.run_installer(
            "codex", "--skills-dir", skills_directory
        )
        before = snapshot_tree(skills_directory / "digital-brain-setup")

        second = self.run_installer(
            "codex", "--skills-dir", skills_directory
        )

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            snapshot_tree(skills_directory / "digital-brain-setup"),
            before,
        )

    def test_reinstall_refuses_different_existing_content(self) -> None:
        skills_directory = self.temp_root / "conflicting-skills"
        first = self.run_installer(
            "claude", "--skills-dir", skills_directory
        )
        installed_skill = skills_directory / "digital-brain-setup"
        changed_file = installed_skill / "SKILL.md"
        changed_file.write_text("用户已有的不同内容\n", encoding="utf-8")
        extra_file = installed_skill / "user-note.md"
        extra_file.write_text("必须保留\n", encoding="utf-8")

        second = self.run_installer(
            "claude", "--skills-dir", skills_directory
        )

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(
            changed_file.read_text(encoding="utf-8"),
            "用户已有的不同内容\n",
        )
        self.assertEqual(extra_file.read_text(encoding="utf-8"), "必须保留\n")

    def test_installation_succeeds_with_network_and_commands_blocked(self) -> None:
        guard_directory = self.temp_root / "network-guard"
        guard_directory.mkdir()
        loaded_marker = guard_directory / "loaded"
        (guard_directory / "sitecustomize.py").write_text(
            "from pathlib import Path\n"
            "import os\n"
            "import socket\n"
            "import subprocess\n"
            "\n"
            "def blocked(*args, **kwargs):\n"
            "    raise RuntimeError('安装器不得访问网络或运行外部命令')\n"
            "\n"
            "socket.socket = blocked\n"
            "socket.create_connection = blocked\n"
            "socket.getaddrinfo = blocked\n"
            "subprocess.Popen = blocked\n"
            "subprocess.run = blocked\n"
            "subprocess.call = blocked\n"
            "subprocess.check_call = blocked\n"
            "subprocess.check_output = blocked\n"
            "os.system = blocked\n"
            "os.popen = blocked\n"
            f"Path({str(loaded_marker)!r}).write_text('已加载', encoding='utf-8')\n",
            encoding="utf-8",
        )
        env = self.base_env.copy()
        previous_python_path = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(guard_directory)
        if previous_python_path:
            env["PYTHONPATH"] += os.pathsep + previous_python_path
        skills_directory = self.temp_root / "offline-skills"

        result = self.run_installer(
            "codex",
            "--skills-dir",
            skills_directory,
            env=env,
        )

        self.assertTrue(loaded_marker.is_file())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_complete_skill_copy(
            skills_directory / "digital-brain-setup"
        )

    def test_readme_and_platform_guides_offer_one_prompt_installation(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        release_url = "https://github.com/stophemo/digital-brain/releases"
        cases = (
            ("codex", ROOT / "guides/codex.md"),
            ("claude", ROOT / "guides/claude-code.md"),
        )
        for platform, guide_path in cases:
            with self.subTest(platform=platform):
                guide = guide_path.read_text(encoding="utf-8")
                command = f"python3 scripts/install_skill.py {platform}"
                self.assertIn(command, readme)
                self.assertIn(command, guide)
                self.assertIn(
                    release_url,
                    guide,
                )
                self.assertIn(release_url, readme)
                self.assertIn("不要改用 main", readme)
                self.assertIn("不要改用 main", guide)
                self.assertNotIn(
                    "git clone https://github.com/stophemo/digital-brain.git",
                    guide,
                )
                self.assertIn("digital-brain-setup/SKILL.md", guide)
                self.assertIn("逐题访谈", guide)


if __name__ == "__main__":
    unittest.main()
