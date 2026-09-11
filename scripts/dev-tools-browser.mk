# Shared browser integration for dev-tools.
# Upstream: https://github.com/gi8lino/dev-tools
# Version: __VERSION__

OPEN_BROWSER := $(DEV_TOOLS_BIN)/open-browser

$(OPEN_BROWSER): | $(DEV_TOOLS_BIN)
	$(call download-dev-tool,open-browser,$@)
