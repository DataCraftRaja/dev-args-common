# Scalable Data Pipelines - Makefile
# Common development and deployment tasks

.PHONY: help install test test-unit test-integration test-contract lint format type-check clean \
        tf-init tf-plan tf-apply tf-destroy \
        k8s-deploy k8s-delete helm-deploy helm-delete \
        run-batch run-streaming run-ml \
        deploy-dev deploy-staging deploy-prod \
        pre-commit docs

# Default target
help:
	@echo "Scalable Data Pipelines - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-contract    - Run contract/schema tests"
	@echo "  make lint             - Run linters (ruff, black --check)"
	@echo "  make format           - Format code (black, ruff --fix)"
	@echo "  make type-check       - Run mypy type checking"
	@echo "  make pre-commit       - Run all pre-commit checks"
	@echo "  make clean            - Clean build artifacts"
	@echo ""
	@echo "Infrastructure (Terraform):"
	@echo "  make tf-init ENV=dev  - Initialize Terraform"
	@echo "  make tf-plan ENV=dev  - Plan Terraform changes"
	@echo "  make tf-apply ENV=dev - Apply Terraform changes"
	@echo "  make tf-destroy ENV=dev - Destroy Terraform resources"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy ENV=dev - Deploy to Kubernetes"
	@echo "  make k8s-delete ENV=dev - Delete from Kubernetes"
	@echo "  make helm-deploy ENV=dev - Deploy with Helm"
	@echo "  make helm-delete ENV=dev - Delete Helm release"
	@echo ""
	@echo "Pipeline Execution:"
	@echo "  make run-batch PIPELINE=name - Run batch pipeline"
	@echo "  make run-streaming PIPELINE=name - Run streaming pipeline"
	@echo "  make run-ml PIPELINE=name - Run ML pipeline"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-dev       - Full deploy to dev"
	@echo "  make deploy-staging   - Full deploy to staging"
	@echo "  make deploy-prod      - Full deploy to prod"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             - Build documentation"
	@echo "  make docs-serve       - Serve documentation locally"

# Variables
ENV ?= dev
PIPELINE ?= example
PYTHON := python3
PIP := pip3
TERRAFORM := terraform
KUBECTL := kubectl
HELM := helm

# Python paths
SRC_DIRS := libs pipelines tests
TEST_DIR := tests

# Install dependencies
install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

# Testing
test: test-unit test-integration test-contract

test-unit:
	$(PYTHON) -m pytest $(TEST_DIR)/unit -v --tb=short -m "unit"

test-integration:
	$(PYTHON) -m pytest $(TEST_DIR)/integration -v --tb=short -m "integration"

test-contract:
	$(PYTHON) -m pytest $(TEST_DIR)/contract -v --tb=short -m "contract"

# Linting & Formatting
lint:
	$(PYTHON) -m ruff check $(SRC_DIRS)
	$(PYTHON) -m black --check $(SRC_DIRS)

format:
	$(PYTHON) -m ruff check --fix $(SRC_DIRS)
	$(PYTHON) -m black $(SRC_DIRS)

type-check:
	$(PYTHON) -m mypy $(SRC_DIRS)

pre-commit: lint type-check test-unit

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf dist build .coverage 2>/dev/null || true

# Terraform
tf-init:
	cd infrastructure/terraform && $(TERRAFORM) init -backend-config="environments/$(ENV)/backend.hcl"

tf-plan:
	cd infrastructure/terraform && $(TERRAFORM) plan -var-file="environments/$(ENV)/terraform.tfvars"

tf-apply:
	cd infrastructure/terraform && $(TERRAFORM) apply -var-file="environments/$(ENV)/terraform.tfvars"

tf-destroy:
	cd infrastructure/terraform && $(TERRAFORM) destroy -var-file="environments/$(ENV)/terraform.tfvars"

# Kubernetes
k8s-deploy:
	$(KUBECTL) apply -k infrastructure/kubernetes/overlays/$(ENV)

k8s-delete:
	$(KUBECTL) delete -k infrastructure/kubernetes/overlays/$(ENV)

helm-deploy:
	$(HELM) upgrade --install scalable-pipelines infrastructure/helm/scalable-pipelines \
		--namespace data-pipelines --create-namespace \
		--values infrastructure/helm/scalable-pipelines/values-$(ENV).yaml

helm-delete:
	$(HELM) uninstall scalable-pipelines --namespace data-pipelines

# Pipeline Execution
run-batch:
	$(PYTHON) -m pipelines.batch.$(PIPELINE).main --config configs/$(ENV)/pipeline.yaml

run-streaming:
	$(PYTHON) -m pipelines.streaming.$(PIPELINE).main --config configs/$(ENV)/pipeline.yaml

run-ml:
	$(PYTHON) -m pipelines.ml.$(PIPELINE).main --config configs/$(ENV)/pipeline.yaml

# Full Deployment
deploy-dev: tf-apply k8s-deploy
	@echo "Deployed to dev environment"

deploy-staging: tf-apply k8s-deploy
	@echo "Deployed to staging environment"

deploy-prod: tf-apply k8s-deploy
	@echo "Deployed to prod environment"

# Documentation
docs:
	cd docs && mkdocs build

docs-serve:
	cd docs && mkdocs serve