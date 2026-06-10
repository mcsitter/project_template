.DEFAULT_GOAL := help

VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/python -m pip

.PHONY: help init venv check clean  test-template

help:  ## Show this help message.
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

check: $(VENV_DIR)/bin/prek  ## Run prek checks.
	$(VENV_PYTHON) -m prek run --all-files

venv: $(VENV_DIR)  # Create virtual environment and install dependencies.
$(VENV_DIR)/bin/prek: venv

$(VENV_DIR): pyproject.toml
	rm -rf $(VENV_DIR)
	python -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip setuptools wheel
	$(VENV_PIP) install -e .
	$(VENV_PIP) freeze --exclude-editable > requirements.txt
	$(VENV_PIP) install -e .[dev]
	$(VENV_PYTHON) -m prek install
	$(VENV_PYTHON) -m prek autoupdate


clean:  ## Clean untracked files (except virtual environment and Python files).
	@FILES="$$(git clean -xdn -e $(VENV_DIR)/ -e '*.py')"; \
	if [ -z "$$FILES" ]; then \
		echo "Nothing to clean."; \
	else \
		printf "%s\n" "$$FILES"; \
		read -p "Delete these files? [y/N] " ANSWER; \
		if [ "$$ANSWER" = "y" ] || [ "$$ANSWER" = "Y" ]; then \
			git clean -xd -f -e $(VENV_DIR)/ -e '*.py'; \
		fi \
	fi

init: clean venv check ## Clean untracked files (except virtual environment and Python files).


$(VENV_DIR)/bin/copier:
	rm -rf $(VENV_DIR)
	python -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip setuptools wheel
	$(VENV_PIP) install copier

test-template: $(VENV_DIR)/bin/copier  ## Test the copier template by applying it to itself
	$(VENV_PYTHON) -m copier copy --defaults --overwrite . .
