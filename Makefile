.DEFAULT_GOAL := help

VERSION_PREFIX ?= v
DEV_TAG := scripts/dev-tag
MAKE_HELP := scripts/make-help

.PHONY: help
help: ## Display this help.
	@$(MAKE_HELP) $(MAKEFILE_LIST)

.PHONY: test
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v

##@ Tagging

.PHONY: current
current: ## Show the current semantic version tag.
	@echo 'dev-tag --prefix "$(VERSION_PREFIX)" current'
	@$(DEV_TAG) --prefix "$(VERSION_PREFIX)" current

.PHONY: patch
patch: ## Create a new patch release tag (x.y.Z+1).
	@echo 'dev-tag --prefix "$(VERSION_PREFIX)" patch'
	@$(DEV_TAG) --prefix "$(VERSION_PREFIX)" patch

.PHONY: minor
minor: ## Create a new minor release tag (x.Y+1.0).
	@echo 'dev-tag --prefix "$(VERSION_PREFIX)" minor'
	@$(DEV_TAG) --prefix "$(VERSION_PREFIX)" minor

.PHONY: major
major: ## Create a new major release tag (X+1.0.0).
	@echo 'dev-tag --prefix "$(VERSION_PREFIX)" major'
	@$(DEV_TAG) --prefix "$(VERSION_PREFIX)" major

.PHONY: push
push: ## Push local tags to the remote repository.
	git push --tags

