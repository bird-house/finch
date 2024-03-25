# Configuration
APP_ROOT := $(abspath $(lastword $(MAKEFILE_LIST))/..)
APP_NAME := finch

WPS_URL = http://localhost:5000

# Used in target refresh-notebooks to make it looks like the notebooks have
# been refreshed from the production server below instead of from the local dev
# instance so the notebooks can also be used as tutorial notebooks.
OUTPUT_URL = https://pavics.ouranos.ca/wpsoutputs/finch

SANITIZE_FILE := https://github.com/Ouranosinc/PAVICS-e2e-workflow-tests/raw/master/notebooks/output-sanitize.cfg

# end of configuration

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
	else:
		match = re.match(r'^## (.*)$$', line)
		if match:
			help = match.groups()[0]
			print("\n%s" % (help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

.DEFAULT_GOAL := help

.PHONY: help
help: ## print this help message. (Default)
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

## Build targets:

.PHONY: install
install: ## install finch application
	@echo "Installing application ..."
	@-bash -c 'pip install -e .'
	@echo "\nStart service with \`make start\` and stop with \`make stop\`."

.PHONY: develop
develop: ## install finch application with development libraries
	@echo "Installing development requirements for tests and docs ..."
	@-bash -c 'pip install -e ".[dev]"'

.PHONY: start
start: ## start finch service as daemon (background process)
	@echo "Starting application ..."
	@-bash -c "$(APP_NAME) start -d"

.PHONY: stop
stop: ## stop finch service
	@echo "Stopping application ..."
	@-bash -c "$(APP_NAME) stop"

.PHONY: restart
restart: stop start  ## restart finch service
	@echo "Restarting application ..."

.PHONY: status
status: ## show status of finch service
	@echo "Showing status ..."
	@-bash -c "$(APP_NAME) status"

.PHONY: clean
clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

.PHONY: clean-build
clean-build: ## remove build artifacts
	@echo "Removing build artifacts ..."
	@-rm -fr build/
	@-rm -fr dist/
	@-rm -fr .eggs/
	@-find . -name '*.egg-info' -exec rm -fr {} +
	@-find . -name '*.egg' -exec rm -f {} +
	@-find . -name '*.log' -exec rm -fr {} +
	@-find . -name '*.sqlite' -exec rm -fr {} +

.PHONY: clean-pyc
clean-pyc: ## remove Python file artifacts
	@echo "Removing Python file artifacts ..."
	@-find . -name '*.pyc' -exec rm -f {} +
	@-find . -name '*.pyo' -exec rm -f {} +
	@-find . -name '*~' -exec rm -f {} +
	@-find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test: ## remove test and coverage artifacts
	@echo "Removing test artifacts ..."
	@-rm -fr .pytest_cache

.PHONY: clean-dist
clean-dist: clean  ## remove git ignored files and directories
	@echo "Running 'git clean' ..."
	@git diff --quiet HEAD || echo "There are uncommitted changes! Aborting 'git clean' ..."
	## do not use git clean -e/--exclude here, add them to .gitignore instead
	@-git clean -dfx

.PHONY: clean-docs
clean-docs: ## remove documentation artifacts
	@echo "Removing documentation artifacts ..."
	$(MAKE) -C docs clean

.PHONY: lint
lint: ## check style
	@echo "Running pre-commit-configured code style checks ..."
	@bash -c 'pre-commit run --all-files'

## Test targets:

.PHONY: test
test: ## run tests quickly with the default Python
	@echo "Running tests (skip slow and online tests) ..."
	@bash -c 'pytest -v -m "not slow and not online" tests/'

.PHONY: test-all
test-all:
	@echo "Running all tests (including slow and online tests) ..."
	@bash -c 'pytest -v tests/'

.PHONY: test-notebooks
test-notebooks: notebook-sanitizer  ## run notebook-based tests
	@echo "Running notebook-based tests"
	@bash -c "env WPS_URL=$(WPS_URL) pytest --nbval --rootdir tests/ --verbose $(CURDIR)/docs/source/notebooks/ --nbval-sanitize-with $(CURDIR)/docs/source/output-sanitize.cfg --ignore $(CURDIR)/docs/source/notebooks/.ipynb_checkpoints"

.PHONY: test-notebooks-lax
test-notebooks-lax: notebook-sanitizer  ## run tests on notebooks but don't be so strict about outputs
	@echo "Running notebook-based tests"
	@bash -c "env WPS_URL=$(WPS_URL) pytest --nbval-lax --rootdir tests/ --verbose $(CURDIR)/docs/source/notebooks/ --ignore $(CURDIR)/docs/source/notebooks/.ipynb_checkpoints"

.PHONY: coverage
coverage: ## check code coverage quickly with the default Python
	@bash -c 'coverage run --source finch -m pytest'
	@bash -c 'coverage report -m'
	@bash -c 'coverage html'
	$(BROWSER) htmlcov/index.html

## Sphinx targets:

.PHONY: docs
docs: clean-docs ## generate Sphinx HTML documentation, including API docs
	@echo "Generating docs with Sphinx ..."
	$(MAKE) -C docs html
	@echo "Open your browser to: file:/$(APP_ROOT)/docs/build/html/index.html"
	## do not execute xdg-open automatically since it hangs ReadTheDocs and job does not complete
	@echo "xdg-open $(APP_ROOT)/docs/build/html/index.html"

.PHONY: servedocs
servedocs: docs ## compile the docs watching for changes
	@echo "Compiling the docs and watching for changes ..."
	@watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

.PHONY: notebook-sanitizer
notebook-sanitizer: ## sanitize notebooks with configuration file
	@echo "Copying notebook output sanitizer ..."
	@-bash -c "curl -L $(SANITIZE_FILE) -o $(CURDIR)/docs/source/output-sanitize.cfg --silent"

.PHONY: refresh-notebooks
refresh-notebooks: ## refreshing all notebook outputs under docs/source/notebooks
	@echo "Refresh all notebook outputs under docs/source/notebooks"
	@bash -c 'for nb in $(CURDIR)/docs/source/notebooks/*.ipynb; do WPS_URL="$(WPS_URL)" jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=60 --output "$$nb" "$$nb"; sed -i "s@$(WPS_URL)/outputs/@$(OUTPUT_URL)/@g" "$$nb"; done; cd $(APP_ROOT)'

## Deployment targets:

.PHONY: dist
dist: clean ## build source and wheel package
	@echo "Building source and wheel package ..."
	@-python setup.py sdist
	@-python setup.py bdist_wheel
	@-bash -c 'ls -l dist/'

release: dist ## upload source and wheel packages
	@echo "Uploading source and wheel packages ..."
	@bash -c 'twine upload dist/*'
