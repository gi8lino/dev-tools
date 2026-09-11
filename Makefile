.DEFAULT_GOAL := help

DEV_TOOLS_BIN := scripts

include make/dev-tools.mk
include make/dev-tools-tag.mk
include make/dev-tools-help.mk
include make/dev-tools-port.mk
include make/dev-tools-browser.mk

# renovate: datasource=github-releases depName=gi8lino/lore
LORE_VERSION ?= v0.14.0
LORE := bin/lore
LORE_ASSET ?= lore_{version}_{os}_{arch}.tar.gz

SITE_CONFIG ?= docs/site.toml
SITE_PORT ?= $(call dev-port,site)
SITE_URL := http://127.0.0.1:$(SITE_PORT)/

##@ Development

.PHONY: test
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v

##@ Documentation

.PHONY: lore
lore: $(GITHUB_RELEASE_INSTALL)
	@$(GITHUB_RELEASE_INSTALL) \
		--repo gi8lino/lore \
		--tag "$(LORE_VERSION)" \
		--asset "$(LORE_ASSET)" \
		--binary lore \
		--target "$(LORE)"

.PHONY: open
open: $(DEV_PORT) $(OPEN_BROWSER) ## Open the documentation site once it responds.
	$(call run-tool,$(OPEN_BROWSER),"$(SITE_URL)")

.PHONY: site
site: lore ## Build the documentation site with Lore.
	$(LORE) build --config "$(SITE_CONFIG)"

.PHONY: site-serve
site-serve: lore $(DEV_PORT) $(OPEN_BROWSER) ## Build, serve, and open the documentation site locally.
	$(LORE) build \
		--config "$(SITE_CONFIG)" \
		--site-url "$(SITE_URL)"
	@echo "Serving dev-tools documentation at $(SITE_URL)"
	@$(OPEN_BROWSER) "$(SITE_URL)" & \
	python3 -m http.server $(SITE_PORT) --bind 127.0.0.1 --directory docs/site
