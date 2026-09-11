# Getting started

A consuming repository only needs to commit the core `dev-tools.mk` bootstrap file. Optional Make modules and their executables are downloaded from the pinned dev-tools release when Make needs them.

## Install the bootstrap

Choose a release and download its `dev-tools.mk` into the project-local `bin` directory:

```sh
version=v0.6.0
mkdir -p bin
curl -fL \
  "https://github.com/gi8lino/dev-tools/releases/download/${version}/dev-tools.mk" \
  -o bin/dev-tools.mk
```

Commit this bootstrap file with the project.

## Configure the Makefile

Set the release version before including the core file, then include only the feature modules the project uses:

```makefile
.DEFAULT_GOAL := help

# renovate: datasource=github-releases depName=gi8lino/dev-tools
DEV_TOOLS_VERSION ?= v0.6.0

include bin/dev-tools.mk
include $(call dev-tools-module,tag)
include $(call dev-tools-module,port)
include $(call dev-tools-module,browser)
include $(call dev-tools-module,help)
```

The core maps each feature module to a version-specific cache below `bin/.dev-tools/<version>/`. If an included module is missing, GNU Make builds that included Makefile by downloading the matching release asset and then reparses the Makefiles. Executables are fetched lazily when a target depends on them.

For example, after the first `make patch` the relevant files can look like:

```text
bin/
├── dev-tools.mk
└── .dev-tools/
    └── v0.6.0/
        ├── dev-tools-tag.mk
        └── dev-tag
```

Only explicitly included modules are downloaded.

## Ignore generated state

Keep the bootstrap file under version control while ignoring downloaded modules, binaries, and port state:

```gitignore
/bin/*
!/bin/dev-tools.mk
/.dev-ports.json
/.dev-ports.json.lock
```

## Updating dev-tools

Change `DEV_TOOLS_VERSION` to select another release. The cache is keyed by version, so a version change uses another directory rather than relying on file modification times. Older cached versions may remain in place and are reusable if the project switches back.

`bin/dev-tools.mk` is the bootstrap itself. When adopting a dev-tools release that changes the core, replace the committed bootstrap with that release's `dev-tools.mk` as well.

Continue with [Make modules and targets](make-modules.md) for module-specific usage.
