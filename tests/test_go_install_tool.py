#!/usr/bin/env python3
"""Exercise versioned Go tool installation without downloading modules."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class GoInstallToolTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.helper = Path(__file__).resolve().parent.parent / "scripts" / "go-install-tool"
        self.fake_bin = self.root / "fake-bin"
        self.fake_bin.mkdir()
        self.log = self.root / "go.log"
        self.fake_go = self.fake_bin / "go"
        self.fake_go.write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            "printf '%s\\n' \"$*\" >> \"$GO_INSTALL_LOG\"\n"
            "if [ \"${FAKE_GO_FAIL:-0}\" = 1 ]; then exit 2; fi\n"
            "package=$2\n"
            "name=${package%@*}\n"
            "name=${name##*/}\n"
            "printf '#!/bin/sh\\n' > \"$GOBIN/$name\"\n"
            "chmod +x \"$GOBIN/$name\"\n"
        )
        self.fake_go.chmod(0o755)

    def environment(self, fail=False):
        env = os.environ.copy()
        env["PATH"] = f"{self.fake_bin}{os.pathsep}{env['PATH']}"
        env["GO_INSTALL_LOG"] = str(self.log)
        if fail:
            env["FAKE_GO_FAIL"] = "1"
        return env

    def call(self, target, *, fail=False, check=True):
        return subprocess.run(
            [
                sys.executable,
                str(self.helper),
                "--target", str(target),
                "--package", "example.com/tools/tool",
                "--tool-version", "v1.2.3",
            ],
            text=True, capture_output=True, check=check, env=self.environment(fail),
        )

    def test_installs_versioned_binary_and_links_stable_name(self):
        target = self.root / "bin" / "tool"
        result = self.call(target)
        versioned = self.root / "bin" / "tool-v1.2.3"
        self.assertTrue(versioned.is_file())
        self.assertTrue(target.is_symlink())
        self.assertEqual(os.readlink(target), "tool-v1.2.3")
        self.assertEqual(self.log.read_text().strip(), "install example.com/tools/tool@v1.2.3")
        self.assertIn("Downloading example.com/tools/tool@v1.2.3", result.stdout)

    def test_existing_versioned_binary_is_reused_without_go_install(self):
        target = self.root / "bin" / "tool"
        target.parent.mkdir()
        versioned = self.root / "bin" / "tool-v1.2.3"
        versioned.write_text("existing\n")
        self.call(target)
        self.assertTrue(target.is_symlink())
        self.assertEqual(os.readlink(target), "tool-v1.2.3")
        self.assertFalse(self.log.exists())

    def test_failed_go_install_returns_error_without_versioned_binary(self):
        target = self.root / "bin" / "tool"
        result = self.call(target, fail=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("go-install-tool:", result.stderr)
        self.assertFalse((self.root / "bin" / "tool-v1.2.3").exists())

    def test_version(self):
        result = subprocess.run(
            [sys.executable, str(self.helper), "--version"],
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(result.stdout.strip(), "go-install-tool 0.3.0")


if __name__ == "__main__":
    unittest.main()
