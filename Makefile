.DEFAULT_GOAL := help

DEV_TOOLS_BIN := scripts

include make/dev-tools.mk
include make/dev-tools-tag.mk
include make/dev-tools-help.mk

##@ Development

.PHONY: test
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v
