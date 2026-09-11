.DEFAULT_GOAL := help

DEV_TOOLS_BIN := scripts

include make/dev-tools.mk
include make/dev-tools-tag.mk
include make/dev-tools-help.mk

LORE ?= lore
SITE_CONFIG ?= docs/site.toml
SITE_PORT ?= 8081

##@ Development

.PHONY: test
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v

##@ Documentation

.PHONY: site
site: ## Build the documentation site with Lore.
	$(LORE) build --config "$(SITE_CONFIG)"

.PHONY: site-serve
site-serve: ## Build and serve the documentation site locally.
	$(LORE) build \
		--config "$(SITE_CONFIG)" \
		--site-url "http://127.0.0.1:$(SITE_PORT)/"
	@echo "Serving dev-tools documentation at http://127.0.0.1:$(SITE_PORT)/"
	python3 -m http.server $(SITE_PORT) --bind 127.0.0.1 --directory docs/site
