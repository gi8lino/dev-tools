.DEFAULT_GOAL := help

include scripts/dev-tools.mk
include $(call dev-tools-module,tag)
include $(call dev-tools-module,help)

##@ Development

.PHONY: test
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v
