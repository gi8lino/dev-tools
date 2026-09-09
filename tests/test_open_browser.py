#!/usr/bin/env python3
"""Exercise waiting for an endpoint and opening the default browser."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from threading import Thread
import unittest


class Handler(BaseHTTPRequestHandler):
    status = 204

    def do_HEAD(self):
        self.send_response(self.status)
        self.end_headers()

    def log_message(self, format, *args):
        pass


class OpenBrowserTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        directory = Path(self.directory.name)
        self.helper = Path(__file__).resolve().parent.parent / "open-browser"
        self.capture = directory / "opened-url.txt"
        self.browser = directory / "browser"
        self.browser.write_text('#!/bin/sh\nprintf "%s\\n" "$1" > "$OPEN_BROWSER_CAPTURE"\n')
        self.browser.chmod(0o755)

    def environment(self):
        env = os.environ.copy()
        env["BROWSER"] = f"{self.browser} %s"
        env["OPEN_BROWSER_CAPTURE"] = str(self.capture)
        return env

    def call(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(self.helper), *args],
            text=True, capture_output=True, check=check, env=self.environment(),
        )

    def serve(self, status=204):
        Handler.status = status
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}/"

    def test_opens_url_after_server_responds(self):
        url = self.serve()
        self.call("--timeout", "2", "--interval", "0.01", url)
        self.assertEqual(self.capture.read_text().strip(), url)

    def test_http_error_still_counts_as_reachable(self):
        url = self.serve(status=404)
        self.call("--timeout", "2", "--interval", "0.01", url)
        self.assertEqual(self.capture.read_text().strip(), url)

    def test_times_out_when_server_is_unreachable(self):
        with socket.socket() as blocker:
            blocker.bind(("127.0.0.1", 0))
            port = blocker.getsockname()[1]
            result = self.call(
                "--timeout", "0.05", "--interval", "0.01",
                f"http://127.0.0.1:{port}/", check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timed out waiting", result.stderr)
        self.assertFalse(self.capture.exists())

    def test_rejects_non_http_url(self):
        result = self.call("file:///tmp/index.html", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("URL must use http or https", result.stderr)
        self.assertFalse(self.capture.exists())

    def test_version_does_not_open_browser(self):
        result = self.call("--version")
        self.assertEqual(result.stdout.strip(), "open-browser 0.2.0")
        self.assertFalse(self.capture.exists())


if __name__ == "__main__":
    unittest.main()
