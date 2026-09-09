.DEFAULT_GOAL := help

.PHONY: test help
test: ## Run all dev-tools tests.
	python3 -m unittest discover -s tests -v

help: ## Show available commands.
	@echo "make test                  Run the test suite"
	@echo "./dev-port NAME            Get or allocate a named port"
	@echo "./open-browser URL         Wait for a URL and open it"
