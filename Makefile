.DEFAULT_GOAL := help

.PHONY: test help
test: ## Test persistence, concurrency, overrides, and isolation.
	python3 -m unittest discover -s tests -v

help: ## Show available commands.
	@echo "make test  Run the test suite"
	@echo "python3 dev-port.py NAME  Get or allocate a named port"
