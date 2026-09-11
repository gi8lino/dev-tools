# dev-tools

Small, reusable development helpers for macOS and Linux. The tools require Python 3.8 or newer and use only the standard library.

Maintained source scripts live in `scripts/`; release assets keep their short executable names. `scripts/dev-tools.mk` provides the shared GNU Make integration.

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

Generate Makefile help output from targets documented with `##`.

```makefile
.DEFAULT_GOAL := help

include bin/dev-tools.mk

.PHONY: test
test: ## Run all tests.
	python3 -m unittest discover -s tests -v

.PHONY: help
help: ## Display this help.
	@$(MAKE_HELP) $(MAKEFILE_LIST)
```

Running `make` or `make help` displays:

```text
Usage:
  make <target>

  test                 Run all tests.
  help                 Display this help.
```

Multiple Makefiles can be passed to the command:

```sh
./scripts/make-help Makefile build.mk
```

When no file is specified, `make-help` reads `Makefile` from the current directory.

Use `##@` headings to group related targets:

```makefile
##@ Development

test: ## Run all tests.
	...

lint: ## Run the linter.
	...

##@ Release

patch: ## Create a patch release.
	...

minor: ## Create a minor release.
	...
```

which produces:

```text
Usage:
  make <target>

Development
  test                 Run all tests.
  lint                 Run the linter.

Release
  patch                Create a patch release.
  minor                Create a minor release.
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

### `dev-tools.mk`

Shared GNU Make integration for projects that install the release assets together in one directory.

```makefile
include bin/dev-tools.mk
```

The include determines its own directory and exposes the paths to the bundled tools:

```makefile
$(DEV_TOOLS_BIN)
$(DEV_PORT)
$(OPEN_BROWSER)
$(DEV_TAG)
$(MAKE_HELP)
$(GO_INSTALL_TOOL)
```

It also provides `dev-port` for resolving named development ports and `run-tool` for executing a local tool while displaying only its executable name:

```makefile
APP_PORT ?= $(call dev-port,app)

.PHONY: patch
patch:
	$(call run-tool,$(DEV_TAG),--prefix "v" patch)
```

For an include installed at `bin/dev-tools.mk`, `DEV_TOOLS_BIN` resolves to `bin`, so projects do not need their own `LOCALBIN` or repeated dev-tools path variables.

## Releases

Each release contains five executable tools, the shared Make include, and checksums:

```text
dev-port
open-browser
dev-tag
make-help
go-install-tool
dev-tools.mk
checksums.txt
```

A pushed `v*` tag creates the GitHub release and uploads all six reusable assets plus the checksum file.

Use the Make targets to create semantic version tags:

```sh
make current
make patch
make minor
make major
```

For example:

```text
$ make current
dev-tag --prefix "v" current
v0.4.0

$ make patch
dev-tag --prefix "v" patch
Tagged v0.4.1
```

The repository Makefile uses the same `scripts/dev-tools.mk` integration that consuming projects use, so the real `scripts/dev-tag` path remains hidden from the displayed command.

Tags are created locally. Push them explicitly:

```sh
make push
```

which runs:

```sh
git push --tags
```

The scripts and `dev-tools.mk` contain release version metadata. The release workflow replaces the version placeholder, verifies every asset, and rejects unresolved placeholders.

To use tags without the default `v` prefix:

```sh
make patch VERSION_PREFIX=
```

## Installing a Release

To install a pinned release into a repository-local `bin` directory:

```sh
version=v0.4.0

mkdir -p bin

for asset in dev-port open-browser dev-tag make-help go-install-tool dev-tools.mk; do
  curl -fL \
    "https://github.com/gi8lino/dev-tools/releases/download/${version}/${asset}" \
    -o "bin/${asset}"
done

chmod +x \
  bin/dev-port \
  bin/open-browser \
  bin/dev-tag \
  bin/make-help \
  bin/go-install-tool
```

This makes the release easy to pin with Renovate:

```makefile
# renovate: datasource=github-releases depName=gi8lino/dev-tools
DEV_TOOLS_VERSION ?= v0.4.0
```

`dev-tools.mk` is the Make integration layer, not the initial downloader. Make sure it exists before parsing a Makefile that includes it, for example by installing the pinned release as part of the repository's bootstrap process.

## Use from Make

Once the release is installed together in `bin`, projects only need to include the shared Make file. The include derives all bundled tool paths from its own location.

```makefile
.DEFAULT_GOAL := help

include bin/dev-tools.mk

VERSION_PREFIX ?= v

# renovate: datasource=github-releases depName=gi8lino/dev-tools
DEV_TOOLS_VERSION ?= v0.4.0

APP_PORT ?= $(call dev-port,app)
DB_PORT ?= $(call dev-port,postgres)

##@ Development

.PHONY: ports
ports: ## Show development ports.
	@$(DEV_PORT) app --port "$(APP_PORT)" > /dev/null
	@$(DEV_PORT) postgres --port "$(DB_PORT)" > /dev/null
	@echo "App: http://127.0.0.1:$(APP_PORT)/"
	@echo "Postgres: 127.0.0.1:$(DB_PORT)"

.PHONY: ports-reset
ports-reset: ## Reset development port assignments.
	$(call run-tool,$(DEV_PORT),--reset)

.PHONY: open
open: ## Open the application in the default browser.
	$(call run-tool,$(OPEN_BROWSER),"http://127.0.0.1:$(APP_PORT)/")

##@ Release

.PHONY: current
current: ## Show the current semantic version tag.
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" current)

.PHONY: patch
patch: ## Create a new patch release tag.
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" patch)

.PHONY: minor
minor: ## Create a new minor release tag.
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" minor)

.PHONY: major
major: ## Create a new major release tag.
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" major)

.PHONY: push
push: ## Push local tags to the remote repository.
	git push --tags

##@ General

.PHONY: help
help: ## Display this help.
	@$(MAKE_HELP) $(MAKEFILE_LIST)
```

For example, even when `DEV_TAG` ultimately refers to a repository-local executable, `make patch` displays:

```text
dev-tag --prefix "v" patch
Tagged v0.7.1
```

The project does not need to repeat `LOCALBIN`, `DEV_PORT`, `OPEN_BROWSER`, `DEV_TAG`, `MAKE_HELP`, or `GO_INSTALL_TOOL`. Those paths belong to the shared integration.

### Installing Go tools

A Go project can use the shared installer and `run-tool` without carrying its own installer macro or path boilerplate:

```makefile
include bin/dev-tools.mk

GOLANGCI_LINT := $(DEV_TOOLS_BIN)/golangci-lint

# renovate: datasource=github-releases depName=golangci/golangci-lint
GOLANGCI_LINT_VERSION ?= v2.13.2

.PHONY: golangci-lint
golangci-lint:
	$(call run-tool,$(GO_INSTALL_TOOL),\
		--target "$(GOLANGCI_LINT)" \
		--package github.com/golangci/golangci-lint/v2/cmd/golangci-lint \
		--tool-version "$(GOLANGCI_LINT_VERSION)")

.PHONY: lint
lint: golangci-lint
	$(call run-tool,$(GOLANGCI_LINT),run)
```

Using `$(GOLANGCI_LINT)` for the actual invocation means the local binary does not need to be added to `PATH`, while `run-tool` keeps the displayed command readable.

Add these entries to projects using `dev-tools`:

```gitignore
/.dev-ports.json
/.dev-ports.json.lock
```

## Development

Run the complete test suite with:

```sh
make test
```

Run the generated Makefile help with:

```sh
make
```

or:

```sh
make help
```

CI runs the test suite on Linux and macOS.

