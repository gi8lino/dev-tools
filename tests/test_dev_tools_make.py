#!/usr/bin/env python3
"""Exercise the modular GNU Make integration."""

import os
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

        self.source = Path(__file__).resolve().parent.parent / "make"
        shutil.copy(self.source / "dev-tools.mk", self.bin / "dev-tools.mk")

        self.release = self.root / "release"
        self.release.mkdir()

        self.fake_bin = self.root / "fake-bin"
        self.fake_bin.mkdir()
        curl = self.fake_bin / "curl"
        curl.write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            "output=\n"
            "url=\n"
            "while [ \"$#\" -gt 0 ]; do\n"
            "  case \"$1\" in\n"
            "    -o) output=$2; shift 2 ;;\n"
            "    --fail|--silent|--show-error|--location) shift ;;\n"
            "    *) url=$1; shift ;;\n"
            "  esac\n"
            "done\n"
            "cp \"$DEV_TOOLS_FAKE_RELEASE/${url##*/}\" \"$output\"\n"
        )
        curl.chmod(0o755)

    def environment(self):
        environment = os.environ.copy()
        environment["PATH"] = f"{self.fake_bin}{os.pathsep}{environment['PATH']}"
        environment["DEV_TOOLS_FAKE_RELEASE"] = str(self.release)
        return environment

    def make(self, target, *, check=True):
        return subprocess.run(
            ["make", "--no-print-directory", target],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=check,
            env=self.environment(),
        )

    def add_release_module(self, name):
        shutil.copy(self.source / name, self.release / name)

    def add_release_tool(self, name, body):
        path = self.release / name
        path.write_text("#!/bin/sh\nset -eu\n" + body)
        path.chmod(0o755)

    def test_core_resolves_paths_relative_to_itself_without_version(self):
        (self.root / "Makefile").write_text(
            "include bin/dev-tools.mk\n"
            "\n"
            ".PHONY: paths\n"
            "paths:\n"
            "\t@printf '%s\\n' '$(DEV_TOOLS_ROOT)' '$(DEV_TOOLS_BIN)' '$(GO_INSTALL_TOOL)' '$(GITHUB_RELEASE_INSTALL)'\n"
        )

        result = self.make("paths")

        self.assertEqual(
            result.stdout.splitlines(),
            ["bin", "bin", "bin/go-install-tool", "bin/github-release-install"],
        )

    def test_core_uses_version_specific_cache_when_version_is_set(self):
        (self.root / "Makefile").write_text(
            "DEV_TOOLS_VERSION := v1.2.3\n"
            "include bin/dev-tools.mk\n"
            "\n"
            ".PHONY: paths\n"
            "paths:\n"
            "\t@printf '%s\\n' '$(DEV_TOOLS_BIN)' '$(call dev-tools-module,tag)'\n"
        )

        result = self.make("paths")

        self.assertEqual(
            result.stdout.splitlines(),
            [
                "bin/.dev-tools/v1.2.3",
                "bin/.dev-tools/v1.2.3/dev-tools-tag.mk",
            ],
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

    def test_core_downloads_github_release_installer(self):
        self.add_release_tool("github-release-install", "printf 'installer\\n'\n")

        (self.root / "Makefile").write_text(
            "DEV_TOOLS_VERSION := v1.2.3\n"
            "include bin/dev-tools.mk\n"
            "\n"
            ".PHONY: installer\n"
            "installer: $(GITHUB_RELEASE_INSTALL)\n"
            "\t@$(GITHUB_RELEASE_INSTALL)\n"
        )

        result = self.make("installer")

        self.assertIn(
            "Downloading gi8lino/dev-tools v1.2.3 github-release-install",
            result.stdout,
        )
        self.assertEqual(result.stdout.splitlines()[-1], "installer")
        installed = self.bin / ".dev-tools" / "v1.2.3" / "github-release-install"
        self.assertTrue(installed.is_file())
        self.assertTrue(os.access(installed, os.X_OK))

    def test_missing_tag_module_and_tool_are_downloaded_automatically(self):
        self.add_release_module("dev-tools-tag.mk")
        self.add_release_tool("dev-tag", "printf 'tag %s\\n' \"$*\"\n")

        (self.root / "Makefile").write_text(
            ".DEFAULT_GOAL := patch\n"
            "DEV_TOOLS_VERSION ?= v1.2.3\n"
            "include bin/dev-tools.mk\n"
            "include $(call dev-tools-module,tag)\n"
        )

        result = self.make("patch")

        self.assertIn(
            "Downloading gi8lino/dev-tools v1.2.3 dev-tools-tag.mk",
            result.stdout,
        )
        self.assertIn(
            "Downloading gi8lino/dev-tools v1.2.3 dev-tag",
            result.stdout,
        )
        self.assertIn('dev-tag --prefix "v" patch', result.stdout)
        self.assertIn("tag --prefix v patch", result.stdout)

        cache = self.bin / ".dev-tools" / "v1.2.3"
        self.assertTrue((cache / "dev-tools-tag.mk").is_file())
        self.assertTrue((cache / "dev-tag").is_file())
        self.assertTrue(os.access(cache / "dev-tag", os.X_OK))

        cached = self.make("patch")
        self.assertNotIn("Downloading gi8lino/dev-tools", cached.stdout)

    def test_version_change_uses_a_new_cache_without_mtime_checks(self):
        self.add_release_module("dev-tools-tag.mk")
        self.add_release_tool("dev-tag", "printf 'tag %s\\n' \"$*\"\n")

        makefile = self.root / "Makefile"
        makefile.write_text(
            "DEV_TOOLS_VERSION := v1.2.3\n"
            "include bin/dev-tools.mk\n"
            "include $(call dev-tools-module,tag)\n"
        )
        self.make("patch")

        makefile.write_text(
            "DEV_TOOLS_VERSION := v1.2.4\n"
            "include bin/dev-tools.mk\n"
            "include $(call dev-tools-module,tag)\n"
        )
        result = self.make("patch")

        self.assertIn(
            "Downloading gi8lino/dev-tools v1.2.4 dev-tools-tag.mk",
            result.stdout,
        )
        self.assertIn(
            "Downloading gi8lino/dev-tools v1.2.4 dev-tag",
            result.stdout,
        )
        self.assertTrue(
            (self.bin / ".dev-tools" / "v1.2.3" / "dev-tools-tag.mk").is_file()
        )
        self.assertTrue(
            (self.bin / ".dev-tools" / "v1.2.4" / "dev-tools-tag.mk").is_file()
        )
        self.assertTrue((self.bin / ".dev-tools" / "v1.2.4" / "dev-tag").is_file())

    def test_port_module_downloads_tool_before_port_is_resolved(self):
        self.add_release_module("dev-tools-port.mk")
        self.add_release_tool("dev-port", "printf '5801\\n'\n")

        (self.root / "Makefile").write_text(
            "DEV_TOOLS_VERSION := v1.2.3\n"
            "include bin/dev-tools.mk\n"
            "include $(call dev-tools-module,port)\n"
            "APP_PORT = $(call dev-port,app)\n"
            "\n"
            ".PHONY: port\n"
            "port: $(DEV_PORT)\n"
            "\t@printf '%s\\n' '$(APP_PORT)'\n"
        )

        result = self.make("port")

        self.assertIn(
            "Downloading gi8lino/dev-tools v1.2.3 dev-tools-port.mk",
            result.stdout,
        )
        self.assertIn(
            "Downloading gi8lino/dev-tools v1.2.3 dev-port",
            result.stdout,
        )
        self.assertEqual(result.stdout.splitlines()[-1], "5801")


if __name__ == "__main__":
    unittest.main()
