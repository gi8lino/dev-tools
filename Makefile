.DEFAULT_GOAL := help

include scripts/dev-tools.mk

VERSION_PREFIX ?= v

.PHONY: help
help: ## Display this help.
	@$(MAKE_HELP) $(MAKEFILE_LIST)

.PHONY: test
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v

##@ Tagging

.PHONY: current
current: ## Show the current semantic version tag.
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" current)

.PHONY: patch
patch: ## Create a new patch release tag (x.y.Z+1).
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" patch)

.PHONY: minor
minor: ## Create a new minor release tag (x.Y+1.0).
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" minor)

.PHONY: major
major: ## Create a new major release tag (X+1.0.0).
	$(call run-tool,$(DEV_TAG),--prefix "$(VERSION_PREFIX)" major)

.PHONY: push
push: ## Push local tags to the remote repository.
	git push --tags
