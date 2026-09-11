.DEFAULT_GOAL := help

DEV_TOOLS_BIN := scripts

include make/dev-tools.mk
include make/dev-tools-tag.mk
include make/dev-tools-help.mk

# renovate: datasource=github-releases depName=gi8lino/lore
LORE_VERSION ?= v0.13.0
LORE_OS := $(shell uname -s | tr '[:upper:]' '[:lower:]')
LORE_ARCH := $(shell uname -m | sed -e 's/^x86_64$$/amd64/' -e 's/^aarch64$$/arm64/')
LORE_CACHE := .cache/lore/$(LORE_VERSION)/$(LORE_OS)_$(LORE_ARCH)
LORE := $(LORE_CACHE)/lore
SITE_CONFIG ?= docs/site.toml
SITE_PORT ?= 8081

##@ Development

.PHONY: test
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v

##@ Documentation

.PHONY: site
site: $(LORE) ## Build the documentation site with Lore.
	$(LORE) build --config "$(SITE_CONFIG)"

.PHONY: site-serve
site-serve: $(LORE) ## Build and serve the documentation site locally.
	$(LORE) build \
		--config "$(SITE_CONFIG)" \
		--site-url "http://127.0.0.1:$(SITE_PORT)/"
	@echo "Serving dev-tools documentation at http://127.0.0.1:$(SITE_PORT)/"
	python3 -m http.server $(SITE_PORT) --bind 127.0.0.1 --directory docs/site

$(LORE):
	@set -eu; \
	case "$(LORE_OS)" in \
		darwin|linux) ;; \
		*) echo "Unsupported Lore operating system: $(LORE_OS)" >&2; exit 1 ;; \
	esac; \
	case "$(LORE_ARCH)" in \
		amd64|arm64) ;; \
		*) echo "Unsupported Lore architecture: $(LORE_ARCH)" >&2; exit 1 ;; \
	esac; \
	version="$(patsubst v%,%,$(LORE_VERSION))"; \
	archive="lore_$${version}_$(LORE_OS)_$(LORE_ARCH).tar.gz"; \
	checksums="lore_$${version}_checksums.txt"; \
	base="https://github.com/gi8lino/lore/releases/download/$(LORE_VERSION)"; \
	tmpdir="$(LORE_CACHE).tmp"; \
	rm -rf "$$tmpdir"; \
	mkdir -p "$$tmpdir" "$(LORE_CACHE)"; \
	trap 'rm -rf "$$tmpdir"' EXIT INT TERM; \
	echo "Downloading gi8lino/lore $(LORE_VERSION) $$archive"; \
	curl --fail --silent --show-error --location \
		"$$base/$$archive" \
		-o "$$tmpdir/$$archive"; \
	curl --fail --silent --show-error --location \
		"$$base/$$checksums" \
		-o "$$tmpdir/$$checksums"; \
	(cd "$$tmpdir" && grep "  $$archive$$" "$$checksums" | shasum -a 256 --check -); \
	tar -xzf "$$tmpdir/$$archive" -C "$$tmpdir"; \
	test -x "$$tmpdir/lore"; \
	mv "$$tmpdir/lore" "$@"; \
	trap - EXIT INT TERM; \
	rm -rf "$$tmpdir"
