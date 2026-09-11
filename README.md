# dev-tools

Small, reusable development helpers for macOS and Linux.

Full documentation: https://gi8lino.github.io/dev-tools/

## Make modules

Keep `bin/dev-tools.mk` in the consuming repository and include only the modules the project needs.

| Module  | Include                            | Provides                                                                     |
| ------- | ---------------------------------- | ---------------------------------------------------------------------------- |
| Core    | `bin/dev-tools.mk`                 | Shared download/run helpers, `go-install-tool`, and `github-release-install` |
| Tagging | `$(call dev-tools-module,tag)`     | `current`, `patch`, `minor`, `major`, `push`                                 |
| Ports   | `$(call dev-tools-module,port)`    | Persistent named development ports                                           |
| Browser | `$(call dev-tools-module,browser)` | Wait for and open a local HTTP endpoint                                      |
| Help    | `$(call dev-tools-module,help)`    | Generated `make help` output                                                 |

## Quick start

Download the bootstrap file from the release you want to use:

```sh
version=v0.7.0
mkdir -p bin
curl -fL \
  "https://github.com/gi8lino/dev-tools/releases/download/${version}/dev-tools.mk" \
  -o bin/dev-tools.mk
```

Then declare the version and modules in your `Makefile`:

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

Missing feature modules and executables are downloaded automatically from the pinned release when Make needs them.

# License

ScreenDeck is licensed under the [Apache License, Version 2.0](LICENSE).
