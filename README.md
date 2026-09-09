# dev-port

Persistent, named TCP ports for local development on macOS and Linux.
Requires Python 3.8 or newer; uses only the standard library.

```sh
python3 dev-port.py postgres
python3 dev-port.py app
python3 dev-port.py pdf
```

The first lookup binds a loopback socket to port zero, lets the OS choose an
available port, and saves it by name. Later calls return the saved port, including
when your service is running. Each project's current directory gets its own
`.dev-ports.json`. Use `--file PATH` to choose another state file.

This lets `make postgres`, `make serve`, and `make open` run independently while
agreeing on the same ports.

## Commands

```sh
python3 dev-port.py postgres              # Get or allocate a port
python3 dev-port.py postgres --port 5433  # Save a fixed port
python3 dev-port.py --reset               # Clear assignments after stopping services
python3 dev-port.py --version
```

Fixed ports are validated but are not checked for availability. Two service names
in one state file cannot share a port. A saved port is never silently changed if
occupied; stop the conflicting service or explicitly update the assignment.

Ports are released after allocation. They are not reserved between lookup and
startup. Separate projects have independent assignments, not a global reservation
pool. Stop services before resetting or changing their ports.

## Use from Make

Keep a copy of `dev-port.py` in your project's `scripts/` directory, pinned to a
release commit. No network access or installation is needed during normal use.
Run Make from the project root (or use `make -C /path/to/project`).

```make
# Set this to the full Git commit of the desired dev-port release.
DEV_PORT_REF := RELEASE_COMMIT

dev-port = $(or $(shell python3 scripts/dev-port.py $(1)),$(error Could not resolve port for $(1)))
APP_PORT ?= $(call dev-port,app)
DB_PORT ?= $(call dev-port,postgres)

.PHONY: ports ports-reset dev-port-update
ports:
	@python3 scripts/dev-port.py app --port "$(APP_PORT)" > /dev/null
	@python3 scripts/dev-port.py postgres --port "$(DB_PORT)" > /dev/null
	@echo "App: http://127.0.0.1:$(APP_PORT)/"
	@echo "Postgres: 127.0.0.1:$(DB_PORT)"

ports-reset:
	python3 scripts/dev-port.py --reset

dev-port-update:
	@set -eu; mkdir -p scripts; tmp=$$(mktemp scripts/dev-port.py.XXXXXX); \
	trap 'rm -f "$$tmp"' EXIT; \
	curl --fail --silent --show-error --location \
	  "https://raw.githubusercontent.com/gi8lino/dev-port/$(DEV_PORT_REF)/dev-port.py" > "$$tmp"; \
	chmod 644 "$$tmp"; mv "$$tmp" scripts/dev-port.py
```

Replace `RELEASE_COMMIT` with the full commit behind your chosen release, then run
`make dev-port-update`. Commit the script and the pin together. To upgrade, change
the pin, run the update target, and review the diff. The `ports` target also saves
Make command-line overrides for future invocations.

Add these entries to each project's `.gitignore`:

```gitignore
/.dev-ports.json
/.dev-ports.json.lock
```

## State safety

A separate lock file serializes concurrent readers and writers. The JSON state
is replaced atomically. Invalid state produces an error and remains unchanged;
`--reset` explicitly clears it. Do not delete the lock file while callers run.

## Development

```sh
make test
```

Tests cover concurrent callers, reuse while occupied, fixed assignments, corrupt
state, reset, and isolation between projects. CI runs on Linux and macOS.
