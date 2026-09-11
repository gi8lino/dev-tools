# Shared development-port integration for dev-tools.
# Upstream: https://github.com/gi8lino/dev-tools
# Version: __VERSION__

DEV_PORT := $(DEV_TOOLS_BIN)/dev-port

$(DEV_PORT): | $(DEV_TOOLS_BIN)
	$(call download-dev-tool,dev-port,$@)

dev-port = $(or $(shell $(DEV_PORT) $(1)),$(error Could not resolve port for $(1)))
