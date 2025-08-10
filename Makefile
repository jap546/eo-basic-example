# ==================================================================================== #
# VARIABLES
# ==================================================================================== #

# Makefile Colors
PURPLE := \033[95m
BLUE := \033[94m
CYAN := \033[96m
GREEN := \033[92m
ORANGE := \033[93m
RED := \033[91m
ENDC := \033[0m
BOLD := \033[1m
UNDERLINE := \033[4m

# ==================================================================================== #
# MAKEFILE TARGETS
# ==================================================================================== #

.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "$(PURPLE)--- 🚀 Installing Environment ---$(ENDC)"
	@echo "$(BLUE) > Creating virtual environment and syncing dependencies...$(ENDC)"
	@uv sync --all-groups
	@echo "$(BLUE) > Installing pre-commit hooks...$(ENDC)"
	@uvx pre-commit install
	@echo "$(GREEN)✅ Install complete! Activate the venv with: source .venv/bin/activate$(ENDC)"

.PHONY: setup
setup: ## Setup project directories etc.
	@echo "$(PURPLE)--- 🚀 Setting up project structure ---$(ENDC)"
	@echo "$(BLUE) > Ensuring project directories exist...$(ENDC)"
	@uv run setup
	@echo "$(GREEN)✅ Setup complete!$(ENDC)"

.PHONY: check
check: ## Run code quality tools.
	@echo "$(PURPLE)--- 🧐 Running Code Quality Checks ---$(ENDC)"
	@echo "$(BLUE) > Checking lock file consistency...$(ENDC)"
	@uv lock --locked
	@echo "$(BLUE) > Linting code with pre-commit...$(ENDC)"
	@uvx pre-commit run -a
	@echo "$(BLUE) > Static type checking with mypy...$(ENDC)"
	@uvx mypy --config-file .github/linters/.mypy.ini .
	@echo "$(BLUE) > Running noxfile...$(ENDC)"
	@uvx nox
	@echo "$GREEN)✅ All checks passed!$(ENDC)"

.PHONY: help
help: ## Display this help message
	@echo "$(BOLD)Makefile Commands:$(ENDC)"
	@uvx python -c "import re; \
	[[print(f'  {m[0]:<20} {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
