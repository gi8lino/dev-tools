#!/usr/bin/env python3
"""Exercise persistence and concurrent callers without touching project state."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest


class DevPortTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name) / "ports.json"
        self.helper = Path(__file__).resolve().parent.parent / "scripts" / "dev-port"

    def call(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(self.helper), "--file", str(self.state), *args],
            text=True, capture_output=True, check=check,
        )

    def test_reuses_port_while_service_is_running(self):
        port = int(self.call("postgres").stdout)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", port))
            listener.listen()
            self.assertEqual(int(self.call("postgres").stdout), port)
            other = int(self.call("app").stdout)
            self.assertNotEqual(other, port)
            with socket.socket() as available:
                available.bind(("127.0.0.1", other))

    def test_parallel_calls_keep_all_names_and_assignments(self):
        names = [f"service-{i % 8}" for i in range(32)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            ports = list(pool.map(lambda name: int(self.call(name).stdout), names))
        saved = json.loads(self.state.read_text())
        self.assertEqual(len(saved), 8)
        self.assertEqual(len(set(saved.values())), 8)
        for name, port in zip(names, ports):
            self.assertEqual(port, saved[name])

    def test_fixed_port_is_saved_and_cannot_be_shared(self):
        self.assertEqual(self.call("app", "--port", "5801").stdout.strip(), "5801")
        self.assertEqual(self.call("app").stdout.strip(), "5801")
        self.assertNotEqual(self.call("postgres", "--port", "5801", check=False).returncode, 0)
        self.assertEqual(json.loads(self.state.read_text()), {"app": 5801})

    def test_invalid_port_does_not_create_state(self):
        self.assertNotEqual(self.call("app", "--port", "0", check=False).returncode, 0)
        self.assertFalse(self.state.exists())

    def test_corrupt_state_is_preserved_until_explicit_reset(self):
        self.state.write_text("broken json")
        self.assertNotEqual(self.call("app", check=False).returncode, 0)
        self.assertEqual(self.state.read_text(), "broken json")
        self.call("--reset")
        self.assertEqual(json.loads(self.state.read_text()), {})
        self.assertGreater(int(self.call("app").stdout), 0)

    def test_default_state_is_in_callers_directory(self):
        result = subprocess.run(
            [sys.executable, str(self.helper), "app"], cwd=self.directory.name,
            text=True, capture_output=True, check=True,
        )
        state = Path(self.directory.name) / ".dev-ports.json"
        self.assertEqual(json.loads(state.read_text()), {"app": int(result.stdout)})

    def test_version_does_not_create_state(self):
        result = subprocess.run(
            [sys.executable, str(self.helper), "--version"], cwd=self.directory.name,
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(result.stdout.strip(), "dev-port __VERSION__")
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_state_files_are_independent(self):
        self.call("app", "--port", "5801")
        original = self.state
        self.state = Path(self.directory.name) / "other.json"
        self.call("app", "--port", "5802")
        self.assertEqual(json.loads(original.read_text()), {"app": 5801})
        self.assertEqual(json.loads(self.state.read_text()), {"app": 5802})


if __name__ == "__main__":
    unittest.main()
