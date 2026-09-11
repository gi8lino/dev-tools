# Shared GNU Make helpers for dev-tools.
# Upstream: https://github.com/gi8lino/dev-tools
# Version: __VERSION__

DEV_TOOLS_BIN := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

DEV_PORT := $(DEV_TOOLS_BIN)/dev-port
OPEN_BROWSER := $(DEV_TOOLS_BIN)/open-browser
DEV_TAG := $(DEV_TOOLS_BIN)/dev-tag
MAKE_HELP := $(DEV_TOOLS_BIN)/make-help
GO_INSTALL_TOOL := $(DEV_TOOLS_BIN)/go-install-tool

dev-port = $(or $(shell $(DEV_PORT) $(1)),$(error Could not resolve port for $(1)))

# Run a local tool while displaying only its executable name.
define run-tool
@printf '%s\n' '$(notdir $(1)) $(strip $(2))'
@$(1) $(2)
endef
