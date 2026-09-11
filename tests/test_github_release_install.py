#!/usr/bin/env python3
"""Exercise GitHub release binary installation without network access."""

import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


class GitHubReleaseInstallTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.helper = Path(__file__).resolve().parent.parent / "scripts" / "github-release-install"
        self.release_root = self.root / "github"
        self.target = self.root / "bin" / "lore"

    def add_release(self, tag, body):
        version = tag[1:] if tag.startswith("v") else tag
        directory = self.release_root / "gi8lino" / "lore" / "releases" / "download" / tag
        directory.mkdir(parents=True, exist_ok=True)
        archive = directory / f"lore_{version}_linux_amd64.tar.gz"
        source = self.root / f"lore-{tag}"
        source.write_text(body)
        source.chmod(0o755)
        with tarfile.open(archive, "w:gz") as output:
            output.add(source, arcname="lore")
        return archive

    def call(self, tag, *, check=True):
        return subprocess.run(
            [
                sys.executable,
                str(self.helper),
                "--repo", "gi8lino/lore",
                "--tag", tag,
                "--asset", "lore_{version}_{os}_{arch}.tar.gz",
                "--binary", "lore",
                "--target", str(self.target),
                "--os", "linux",
                "--arch", "amd64",
                "--base-url", self.release_root.as_uri(),
            ],
            text=True,
            capture_output=True,
            check=check,
        )

    def test_installs_versioned_binary_and_links_stable_name(self):
        self.add_release("v1.2.3", "#!/bin/sh\nprintf 'v1.2.3\\n'\n")

        result = self.call("v1.2.3")

        versioned = self.target.with_name("lore-v1.2.3")
        self.assertTrue(versioned.is_file())
        self.assertTrue(os.access(versioned, os.X_OK))
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(os.readlink(self.target), "lore-v1.2.3")
        self.assertIn(
            "Downloading gi8lino/lore v1.2.3 lore_1.2.3_linux_amd64.tar.gz",
            result.stdout,
        )
        executed = subprocess.run([self.target], text=True, capture_output=True, check=True)
        self.assertEqual(executed.stdout.strip(), "v1.2.3")

    def test_existing_versioned_binary_is_reused(self):
        archive = self.add_release("v1.2.3", "#!/bin/sh\nprintf 'original\\n'\n")
        self.call("v1.2.3")
        archive.unlink()

        result = self.call("v1.2.3")

        self.assertEqual(result.stdout, "")
        executed = subprocess.run([self.target], text=True, capture_output=True, check=True)
        self.assertEqual(executed.stdout.strip(), "original")

    def test_version_change_keeps_old_binary_and_repoints_symlink(self):
        self.add_release("v1.2.3", "#!/bin/sh\nprintf 'old\\n'\n")
        self.add_release("v1.2.4", "#!/bin/sh\nprintf 'new\\n'\n")
        self.call("v1.2.3")

        self.call("v1.2.4")

        self.assertTrue(self.target.with_name("lore-v1.2.3").is_file())
        self.assertTrue(self.target.with_name("lore-v1.2.4").is_file())
        self.assertEqual(os.readlink(self.target), "lore-v1.2.4")
        executed = subprocess.run([self.target], text=True, capture_output=True, check=True)
        self.assertEqual(executed.stdout.strip(), "new")

    def test_direct_asset_can_be_installed_without_archive_member(self):
        tag = "v2.0.0"
        directory = self.release_root / "example" / "tool" / "releases" / "download" / tag
        directory.mkdir(parents=True)
        asset = directory / "tool-linux-amd64"
        asset.write_text("#!/bin/sh\nprintf 'direct\\n'\n")

        target = self.root / "bin" / "tool"
        subprocess.run(
            [
                sys.executable,
                str(self.helper),
                "--repo", "example/tool",
                "--tag", tag,
                "--asset", "tool-{os}-{arch}",
                "--target", str(target),
                "--os", "linux",
                "--arch", "amd64",
                "--base-url", self.release_root.as_uri(),
            ],
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(os.readlink(target), "tool-v2.0.0")
        executed = subprocess.run([target], text=True, capture_output=True, check=True)
        self.assertEqual(executed.stdout.strip(), "direct")

    def test_missing_binary_fails_without_creating_target(self):
        self.add_release("v1.2.3", "#!/bin/sh\nprintf 'test\\n'\n")

        result = subprocess.run(
            [
                sys.executable,
                str(self.helper),
                "--repo", "gi8lino/lore",
                "--tag", "v1.2.3",
                "--asset", "lore_{version}_{os}_{arch}.tar.gz",
                "--binary", "missing",
                "--target", str(self.target),
                "--os", "linux",
                "--arch", "amd64",
                "--base-url", self.release_root.as_uri(),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("binary not found in archive", result.stderr)
        self.assertFalse(self.target.exists())
        self.assertFalse(self.target.is_symlink())

    def test_version(self):
        result = subprocess.run(
            [sys.executable, str(self.helper), "--version"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "github-release-install __VERSION__")


if __name__ == "__main__":
    unittest.main()
