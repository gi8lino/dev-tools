#!/usr/bin/env python3
"""Exercise semantic version tag creation in isolated Git repositories."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DevTagTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repository = Path(self.directory.name)
        self.helper = Path(__file__).resolve().parent.parent / "scripts" / "dev-tag"
        self.git("init", "-q")
        self.git("config", "user.name", "Dev Tools Test")
        self.git("config", "user.email", "dev-tools@example.com")
        (self.repository / "README.md").write_text("test\n")
        self.git("add", "README.md")
        self.git("commit", "-qm", "initial")

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repository,
            text=True, capture_output=True, check=True,
        ).stdout.strip()

    def call(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(self.helper), *args], cwd=self.repository,
            text=True, capture_output=True, check=check,
        )

    def test_current_defaults_to_zero_without_tags(self):
        self.assertEqual(self.call("current").stdout.strip(), "0.0.0")

    def test_patch_minor_and_major_create_semver_tags(self):
        self.assertEqual(self.call("patch").stdout.strip(), "Tagged v0.0.1")
        self.assertEqual(self.call("minor").stdout.strip(), "Tagged v0.1.0")
        self.assertEqual(self.call("major").stdout.strip(), "Tagged v1.0.0")
        self.assertEqual(self.call("current").stdout.strip(), "v1.0.0")

    def test_custom_empty_prefix_creates_unprefixed_tags(self):
        self.assertEqual(self.call("--prefix", "", "patch").stdout.strip(), "Tagged 0.0.1")
        self.assertEqual(self.git("tag", "--list"), "0.0.1")

    def test_ignores_unrelated_and_non_semver_tags(self):
        self.git("tag", "release-9.9.9")
        self.git("tag", "v1.2")
        self.git("tag", "v1.2.3-beta")
        self.git("tag", "v1.4.2")
        self.assertEqual(self.call("patch").stdout.strip(), "Tagged v1.4.3")

    def test_version(self):
        self.assertEqual(self.call("--version").stdout.strip(), "dev-tag 0.3.0")


if __name__ == "__main__":
    unittest.main()
