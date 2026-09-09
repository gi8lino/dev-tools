# dev-tools

Small, reusable development helpers for macOS and Linux. The tools require
Python 3.8 or newer and use only the standard library.

## Tools

### `dev-port`

Persistent, named TCP ports for local development.

```sh
./dev-port postgres
./dev-port app
./dev-port pdf
```

The first lookup binds a loopback socket to port zero, lets the OS choose an
available port, and saves it by name. Later calls return the saved port, including
when your service is running. Each project's current directory gets its own
`.dev-ports.json`. Use `--file PATH` to choose another state file.

```sh
./dev-port postgres              # Get or allocate a port
./dev-port postgres --port 5433  # Save a fixed port
./dev-port --reset               # Clear assignments after stopping services
./dev-port --version
```

Fixed ports are validated but are not checked for availability. Two service names
in one state file cannot share a port. A saved port is never silently changed if
occupied; stop the conflicting service or explicitly update the assignment.

Ports are released after allocation. They are not reserved between lookup and
startup. Separate projects have independent assignments, not a global reservation
pool. Stop services before resetting or changing their ports.

A separate lock file serializes concurrent readers and writers. The JSON state is
replaced atomically. Invalid state produces an error and remains unchanged;
`--reset` explicitly clears it. Do not delete the lock file while callers run.

### `open-browser`

Wait for an HTTP or HTTPS endpoint to respond, then open it in the default browser.
This is useful for development commands that start a server and browser together.

```sh
./open-browser http://127.0.0.1:8080/
./open-browser --timeout 30 http://127.0.0.1:8080/
./open-browser --version
```

Any HTTP response means the endpoint is reachable, including error responses such
as 401 or 404. Connection errors are retried until the timeout expires.

## Releases

Release assets are executable commands without a `.py` suffix:

```text
dev-port
open-browser
checksums.txt
```

A pushed `v*` tag creates the GitHub release and uploads all three assets.

For example:

```sh
git tag v0.2.0
git push origin v0.2.0
```

To install a pinned release into a repository-local `bin` directory:

```sh
version=v0.2.0
mkdir -p bin
curl -fL "https://github.com/gi8lino/dev-tools/releases/download/${version}/dev-port" -o bin/dev-port
curl -fL "https://github.com/gi8lino/dev-tools/releases/download/${version}/open-browser" -o bin/open-browser
chmod +x bin/dev-port bin/open-browser
```

This makes the tools easy to pin with Renovate:

```make
# renovate: datasource=github-releases depName=gi8lino/dev-tools
DEV_TOOLS_VERSION ?= v0.2.0
```

## Use from Make

```make
LOCALBIN ?= $(CURDIR)/bin
DEV_PORT := $(LOCALBIN)/dev-port
OPEN_BROWSER := $(LOCALBIN)/open-browser

# renovate: datasource=github-releases depName=gi8lino/dev-tools
DEV_TOOLS_VERSION ?= v0.2.0

dev-port = $(or $(shell $(DEV_PORT) $(1)),$(error Could not resolve port for $(1)))
APP_PORT ?= $(call dev-port,app)
DB_PORT ?= $(call dev-port,postgres)

.PHONY: ports ports-reset open
ports:
	@$(DEV_PORT) app --port "$(APP_PORT)" > /dev/null
	@$(DEV_PORT) postgres --port "$(DB_PORT)" > /dev/null
	@echo "App: http://127.0.0.1:$(APP_PORT)/"
	@echo "Postgres: 127.0.0.1:$(DB_PORT)"

ports-reset:
	$(DEV_PORT) --reset

open:
	$(OPEN_BROWSER) "http://127.0.0.1:$(APP_PORT)/"
```

Add these entries to projects using `dev-port`:

```gitignore
/.dev-ports.json
/.dev-ports.json.lock
```

## Development

```sh
make test
```

CI runs the test suite on Linux and macOS.
