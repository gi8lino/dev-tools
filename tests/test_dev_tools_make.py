#!/usr/bin/env python3
"""Exercise the shared GNU Make integration."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class DevToolsMakeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()

        source = Path(__file__).resolve().parent.parent / "scripts" / "dev-tools.mk"
        shutil.copy(source, self.bin / "dev-tools.mk")

    def make(self, target):
        return subprocess.run(
            ["make", "--no-print-directory", target],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=True,
        )

    def test_tool_paths_are_relative_to_the_shared_include(self):
        (self.root / "Makefile").write_text(
            "include bin/dev-tools.mk\n"
            "\n"
            ".PHONY: paths\n"
            "paths:\n"
            "\t@printf '%s\\n' '$(DEV_TOOLS_BIN)' '$(DEV_TAG)' '$(MAKE_HELP)'\n"
        )

        result = self.make("paths")

        self.assertEqual(
            result.stdout.splitlines(),
            ["bin", "bin/dev-tag", "bin/make-help"],
        )

    def test_run_tool_hides_the_executable_path(self):
        tool = self.bin / "example-tool"
        tool.write_text("#!/bin/sh\nprintf 'ran %s\\n' \"$*\"\n")
        tool.chmod(0o755)

        (self.root / "Makefile").write_text(
            "include bin/dev-tools.mk\n"
            "\n"
            ".PHONY: run\n"
            "run:\n"
            "\t$(call run-tool,$(DEV_TOOLS_BIN)/example-tool,--flag value)\n"
        )

        result = self.make("run")

        self.assertEqual(
            result.stdout.splitlines(),
            ["example-tool --flag value", "ran --flag value"],
        )
        self.assertNotIn(str(self.root), result.stdout)


if __name__ == "__main__":
    unittest.main()
