# dev-tools

Small, reusable development helpers for macOS and Linux. The tools require Python 3.8 or newer and use only the standard library.

Maintained source scripts live in `scripts/`; release assets keep their short executable names. GNU Make integration is split into a small core plus optional feature modules.

## Tools

### `dev-port`

Persistent, named TCP ports for local development.

```sh
./scripts/dev-port postgres
./scripts/dev-port app
./scripts/dev-port pdf
```

The first lookup binds a loopback socket to port zero, lets the OS choose an available port, and saves it by name. Later calls return the saved port, including when your service is running.

Each project's current directory gets its own `.dev-ports.json`. Use `--file PATH` to choose another state file.

```sh
./scripts/dev-port postgres              # Get or allocate a port
./scripts/dev-port postgres --port 5433  # Save a fixed port
./scripts/dev-port --reset               # Clear assignments after stopping services
./scripts/dev-port --version
```

Fixed ports are validated but are not checked for availability. Two service names in one state file cannot share a port.

A saved port is never silently changed if occupied; stop the conflicting service or explicitly update the assignment.

Ports are released after allocation. They are not reserved between lookup and startup. Separate projects have independent assignments, not a global reservation pool. Stop services before resetting or changing their ports.

A separate lock file serializes concurrent readers and writers. The JSON state is replaced atomically. Invalid state produces an error and remains unchanged; `--reset` explicitly clears it.

Do not delete the lock file while callers run.

### `open-browser`

Wait for an HTTP or HTTPS endpoint to respond, then open it in the default browser. This is useful for development commands that start a server and browser together.

```sh
./scripts/open-browser http://127.0.0.1:8080/
./scripts/open-browser --timeout 30 http://127.0.0.1:8080/
./scripts/open-browser --version
```

Any HTTP response means the endpoint is reachable, including error responses such as 401 or 404. Connection errors are retried until the timeout expires.

### `dev-tag`

Create lightweight semantic version tags using the latest valid `X.Y.Z` tag in the repository. The default prefix is `v`.

```sh
./scripts/dev-tag current
./scripts/dev-tag patch
./scripts/dev-tag minor
./scripts/dev-tag major
./scripts/dev-tag --prefix "" patch
```

With no matching tags, `current` prints `0.0.0` and the first patch tag is `v0.0.1`.

Unrelated tags and non-semantic-version tags are ignored. `dev-tag` creates the tag locally; pushing tags remains an explicit repository action.

### `make-help`

Generate Makefile help output from targets documented with `##` and section headings documented with `##@`.

```makefile
##@ Development

.PHONY: test
test: ## Run all tests.
	go test ./...
```

### `go-install-tool`

Install a pinned Go tool into a local bin directory, keep the versioned binary, and link the stable binary name to it.

```sh
./scripts/go-install-tool \
  --target ./bin/golangci-lint \
  --package github.com/golangci/golangci-lint/v2/cmd/golangci-lint \
  --tool-version v2.13.2
```

The example creates `bin/golangci-lint-v2.13.2` and links `bin/golangci-lint` to it. Existing versioned binaries are reused instead of being downloaded again.

## GNU Make integration

The Make integration is modular:

```text
dev-tools.mk          Core helpers and go-install-tool
dev-tools-tag.mk      Semantic-version tag targets
dev-tools-port.mk     Named development-port integration
dev-tools-browser.mk  Browser launcher integration
dev-tools-help.mk     Generated Make help target
```

A consuming repository only needs to keep the core file. Feature modules and their executables are downloaded from the pinned release when Make needs them.

A typical repository starts with:

```text
project/
├── Makefile
└── bin/
    └── dev-tools.mk
```

Use a version pin before the includes:

```makefile
.DEFAULT_GOAL := help

# renovate: datasource=github-releases depName=gi8lino/dev-tools
DEV_TOOLS_VERSION ?= v0.5.0

include bin/dev-tools.mk
include $(call dev-tools-module,tag)
include $(call dev-tools-module,port)
include $(call dev-tools-module,browser)
include $(call dev-tools-module,help)
```

`dev-tools.mk` maps each requested module to a version-specific cache directory. If, for example, the tagging module is missing, GNU Make downloads it and then reparses the Makefiles. The module downloads `dev-tag` only when a tagging target needs it.

After running `make patch`, the directory can therefore look like:

```text
bin/
├── dev-tools.mk
└── .dev-tools/
    └── v0.5.0/
        ├── dev-tools-tag.mk
        └── dev-tag
```

Only explicitly included feature modules are fetched.

### Core helpers

`dev-tools.mk` determines its own directory, so consuming projects do not need `LOCALBIN` or repeated absolute tool paths.

It provides:

```makefile
$(DEV_TOOLS_ROOT)
$(DEV_TOOLS_BIN)
$(GO_INSTALL_TOOL)
$(call dev-tools-module,<name>)
$(call download-dev-tool,<asset>,<target>)
$(call run-tool,<executable>,<arguments>)
```

`DEV_TOOLS_ROOT` is the directory containing the committed `dev-tools.mk`. With a version pin, `DEV_TOOLS_BIN` points at `.dev-tools/<version>` below that directory.

`run-tool` keeps Make output readable while still executing the repository-local binary. For example:

```makefile
.PHONY: lint
lint: $(GOLANGCI_LINT)
	$(call run-tool,$(GOLANGCI_LINT),run)
```

can display:

```text
golangci-lint run
```

instead of an absolute path.

`go-install-tool` belongs to the core because projects can use it to install arbitrary pinned Go tools:

```makefile
GOLANGCI_LINT := $(DEV_TOOLS_ROOT)/golangci-lint

# renovate: datasource=github-releases depName=golangci/golangci-lint
GOLANGCI_LINT_VERSION ?= v2.13.2

$(GOLANGCI_LINT): $(GO_INSTALL_TOOL)
	$(call run-tool,$(GO_INSTALL_TOOL),\
		--target "$(GOLANGCI_LINT)" \
		--package github.com/golangci/golangci-lint/v2/cmd/golangci-lint \
		--tool-version "$(GOLANGCI_LINT_VERSION)")

.PHONY: lint
lint: $(GOLANGCI_LINT)
	$(call run-tool,$(GOLANGCI_LINT),run)
```

### Tagging module

Include:

```makefile
include $(call dev-tools-module,tag)
```

The module provides:

```text
make current
make patch
make minor
make major
make push
```

Set a different tag prefix when needed:

```makefile
VERSION_PREFIX ?= v
```

or:

```sh
make patch VERSION_PREFIX=
```

### Port module

Include:

```makefile
include $(call dev-tools-module,port)
```

Then resolve named ports with:

```makefile
APP_PORT = $(call dev-port,app)
DB_PORT = $(call dev-port,postgres)
```

Targets that expand those values should depend on `$(DEV_PORT)` so the executable is available before the recipe is expanded:

```makefile
.PHONY: ports
ports: $(DEV_PORT) ## Show development ports.
	@printf 'App: http://127.0.0.1:%s/\n' '$(APP_PORT)'
	@printf 'Postgres: 127.0.0.1:%s\n' '$(DB_PORT)'
```

### Browser module

Include:

```makefile
include $(call dev-tools-module,browser)
```

Then make the consuming target depend on `$(OPEN_BROWSER)`:

```makefile
.PHONY: open
open: $(DEV_PORT) $(OPEN_BROWSER) ## Open the application.
	$(call run-tool,$(OPEN_BROWSER),"http://127.0.0.1:$(APP_PORT)/")
```

### Help module

Include:

```makefile
include $(call dev-tools-module,help)
```

It provides the `help` target and passes all parsed Makefiles to `make-help`, so targets from included feature modules appear automatically.

Put this before the includes when help should be the default target:

```makefile
.DEFAULT_GOAL := help
```

### Version changes

Downloaded feature modules and dev-tools executables are cached under `bin/.dev-tools/<version>`. Changing `DEV_TOOLS_VERSION` selects a different cache directory, so version changes never depend on filesystem modification times. Older caches can remain in place and are reusable if the project switches back to an earlier pin.

The committed `bin/dev-tools.mk` is the bootstrap/core file itself. When the core changes in a future dev-tools release, replace that committed file with the new release version as part of adopting that release.

### Git ignore

A consuming repository can keep only the bootstrap file under version control:

```gitignore
/bin/*
!/bin/dev-tools.mk
/.dev-ports.json
/.dev-ports.json.lock
```

## Installing the bootstrap

Install `dev-tools.mk` once from the release you want to adopt:

```sh
version=v0.5.0
mkdir -p bin
curl -fL \
  "https://github.com/gi8lino/dev-tools/releases/download/${version}/dev-tools.mk" \
  -o bin/dev-tools.mk
```

Then commit `bin/dev-tools.mk`. The project's `DEV_TOOLS_VERSION` pin controls the automatically downloaded modules and executables.

## Releases

Each release contains the executable tools, all Make modules, and checksums:

```text
dev-port
open-browser
dev-tag
make-help
go-install-tool
dev-tools.mk
dev-tools-tag.mk
dev-tools-port.mk
dev-tools-browser.mk
dev-tools-help.mk
checksums.txt
```

A pushed `v*` tag creates the GitHub release. The workflow replaces each `__VERSION__` placeholder, verifies the executables and Make modules, generates checksums, and uploads the complete asset set.

This repository uses the same modular Make integration itself:

```makefile
include scripts/dev-tools.mk
include $(call dev-tools-module,tag)
include $(call dev-tools-module,help)
```

Create release tags with:

```sh
make current
make patch
make minor
make major
make push
```

## Development

Run the complete test suite with:

```sh
make test
```

Run generated Make help with:

```sh
make
```

CI runs the tests on Linux and macOS.
