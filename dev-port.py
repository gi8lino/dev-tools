#!/usr/bin/env python3
"""Persist named development ports per project (macOS and Linux)."""

# Upstream: https://github.com/gi8lino/dev-port
# Version: 0.1.0

import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="dev-port 0.1.0")
    parser.add_argument("name", nargs="?", help="service name, such as app or postgres")
    parser.add_argument("--file", type=Path, default=Path.cwd() / ".dev-ports.json")
    parser.add_argument("--port", type=int, help="explicitly save a fixed port")
    parser.add_argument("--reset", action="store_true", help="clear assignments after stopping services")
    args = parser.parse_args()
    if args.reset and (args.name or args.port is not None):
        parser.error("--reset cannot be combined with a name or --port")
    if not args.reset and not args.name:
        parser.error("a service name is required")
    if args.port is not None and not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    try:
        # Lock a separate, stable file because the JSON file is replaced atomically.
        with Path(str(args.file) + ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            ports = {}
            if args.file.exists() and not args.reset:
                ports = json.loads(args.file.read_text())
                if not isinstance(ports, dict) or any(
                    not isinstance(name, str) or type(port) is not int or not 1 <= port <= 65535
                    for name, port in ports.items()
                ) or len(set(ports.values())) != len(ports):
                    raise ValueError("invalid saved port assignments")
            # Never reallocate an existing assignment, even while it is occupied.
            if not args.reset and args.port is None and args.name in ports:
                print(ports[args.name])
                return
            if not args.reset:
                if args.port is not None:
                    if any(port == args.port and name != args.name for name, port in ports.items()):
                        raise ValueError("port is already assigned to another service")
                    ports[args.name] = args.port
                elif args.name not in ports:
                    for _ in range(100):
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                            listener.bind(("127.0.0.1", 0))
                            port = listener.getsockname()[1]
                        if port not in ports.values():
                            ports[args.name] = port
                            break
                    else:
                        raise ValueError("could not find an unassigned port")
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", dir=args.file.parent, delete=False) as output:
                    temporary = output.name
                    json.dump(ports, output, indent=2, sort_keys=True)
                    output.write("\n")
                os.replace(temporary, args.file)
                temporary = None
            finally:
                if temporary is not None:
                    os.unlink(temporary)
            if not args.reset:
                print(ports[args.name])
    except (OSError, ValueError) as error:
        parser.exit(1, f"dev-port: {error}\n")


if __name__ == "__main__":
    main()
