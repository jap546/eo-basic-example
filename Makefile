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

.PHONY: test
test: ## Test the code with pytest
	@echo "$(PURPLE)--- 🧪 Running Tests ---$(ENDC)"
	@echo "$(BLUE) > Running pytest with coverage report...$(ENDC)"
	@uv run pytest --cov --cov-config=pyproject.toml --cov-report=xml --color=yes
	@echo "$(GREEN)✅ Tests finished!$(ENDC)"

.PHONY: build
build: ## Build wheel file
	@echo "$(ORANGE)--- 🧹 Cleaning Build Artifacts ---$(ENDC)"
	@rm -rf dist
	@echo "$(GREEN)✅ 'dist' directory removed.$(ENDC)"
	@echo "$(PURPLE)--- 📦 Building Project ---$(ENDC)"
	@echo "$(BLUE) > Creating wheel file...$(ENDC)"
	@uv build --wheel
	@echo "$(GREEN)✅ Build successful! Find the wheel in the '~/dist' directory.$(ENDC)"

.PHONY: download-sedona
download-sedona: ## Download required Sedona JARs
	@echo "$(ORANGE)---  📥 Downloading Apache Sedona JARs ---$(ENDC)"
	@echo "..."
	@./download_sedona.sh
	@echo "$(GREEN)✅ Apache Sedona dependencies downloaded, check the '~/deps/jars' directory.$(ENDC)"

.PHONY: dbx-upload
dbx-upload: download-sedona build ## Deploy artifacts to Databricks
	@echo "$(ORANGE)---  🚀 Uploading artifacts to Databricks ---$(ENDC)"
	@./deploy_artifacts.sh
	@echo "$(GREEN)✅ Artifacts have been uploaded to Databricks.$(ENDC)"

.PHONY: help
help: ## Display this help message
	@echo "$(BOLD)Makefile Commands:$(ENDC)"
	@uvx python -c "import re; \
	[[print(f'  {m[0]:<20} {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
