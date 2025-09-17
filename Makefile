# Boxed Koji - Integration Testing Platform
# Makefile for orchestrating Koji container environment

.PHONY: help build up down logs test clean rebuild status pull-koji setup-db setup-hub

# Default target
.DEFAULT_GOAL := help

# Load environment variables
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default values
KOJI_GIT_REPO ?= https://pagure.io/koji.git
KOJI_BRANCH ?= master
BUILD_ARCH ?= x86_64
COMPOSE_FILE ?= docker-compose.yml
PROJECT_NAME ?= koji-boxed

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo -e "$(BLUE)Boxed Koji - Integration Testing Platform$(NC)"
	@echo -e ""
	@echo -e "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo -e ""
	@echo -e "$(YELLOW)Environment Variables:$(NC)"
	@echo -e "  KOJI_GIT_REPO    - Koji repository URL (default: https://pagure.io/koji.git)"
	@echo -e "  KOJI_BRANCH      - Git branch to use (default: main)"

pull-koji: ## Clone/update Koji repository
	@echo -e "$(BLUE)Pulling Koji repository...$(NC)"
	@if [ -d "koji-src" ]; then \
		echo -e "$(YELLOW)Updating existing repository...$(NC)"; \
		cd koji-src && git fetch origin && git checkout $(KOJI_BRANCH) && git pull origin $(KOJI_BRANCH); \
	else \
		echo -e "$(YELLOW)Cloning repository...$(NC)"; \
		git clone -b $(KOJI_BRANCH) $(KOJI_GIT_REPO) koji-src; \
	fi
	@echo -e "$(GREEN)Koji repository ready$(NC)"

build: pull-koji ## Build all container images
	@echo -e "$(BLUE)Building all container images...$(NC)"
	# we have to explicitly build the common image first because podman-compose build doesn't support additional_context
	podman-compose --profile build build common
	podman-compose build
	@echo -e "$(GREEN)All images built successfully$(NC)"

build-fast: pull-koji ## Build all container images (cached)
	@echo -e "$(BLUE)Building all container images (using cache)...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) build
	@echo -e "$(GREEN)All images built successfully$(NC)"

up: down ## Start all services
	@echo -e "$(BLUE)Starting Koji environment...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) up -d
	@echo -e "$(GREEN)Koji environment started$(NC)"

launch: down ## Start all services in the foreground
	@echo -e "$(BLUE)Starting Koji environment...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) up --build

down: ## Stop all services
	@echo -e "$(BLUE)Stopping Koji environment...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) down
	@echo -e "$(GREEN)Koji environment stopped$(NC)"

restart: down up ## Restart all services

logs: ## Show logs for all services
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f

logs-hub: ## Show logs for Koji Hub
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f koji-hub

logs-worker: ## Show logs for Koji Worker
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f koji-worker

logs-web: ## Show logs for Koji Web
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f koji-web

logs-postgres: ## Show logs for PostgreSQL
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f postgres

logs-kdc: ## Show logs for KDC
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f kdc

logs-nginx: ## Show logs for Nginx
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f nginx

logs-orch: ## Show logs for Keytab Service
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs -f orch-service

status: ## Show status of all services
	@echo -e "$(BLUE)Service Status:$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) ps

list-principals: ## List Kerberos principals
	@echo -e "$(BLUE)Listing Kerberos principals...$(NC)"
	podman-compose exec kdc kadmin.local -q "list_principals"

test-kerberos: ## Test Kerberos authentication
	@echo -e "$(BLUE)Testing Kerberos authentication...$(NC)"
	podman-compose exec kdc kinit admin/admin@KOJI.BOX -w admin_password
	podman-compose exec kdc klist

test: ## Run integration tests
	@echo -e "$(BLUE)Running integration tests...$(NC)"
	@if [ -d "tests/test-scripts" ]; then \
		for script in tests/test-scripts/*.sh; do \
			if [ -x "$$script" ]; then \
				echo -e "$(YELLOW)Running $$script...$(NC)"; \
				$$script; \
			fi; \
		done; \
		echo -e "$(GREEN)Integration tests completed$(NC)"; \
	else \
		echo -e "$(YELLOW)No test scripts found$(NC)"; \
	fi

shell-client: ## Open shell in Koji Client container
	podman-compose exec --user koji --workdir /home/koji koji-client /bin/bash

shell-hub: ## Open shell in Koji Hub container
	podman-compose exec koji-hub /bin/bash

shell-worker: ## Open shell in Koji Worker container
	podman-compose exec koji-worker /bin/bash

shell-web: ## Open shell in Koji Web container
	podman-compose exec koji-web /bin/bash

shell-postgres: ## Open shell in PostgreSQL container
	podman-compose exec postgres /bin/bash

shell-kdc: ## Open shell in KDC container
	podman-compose exec kdc /bin/bash

shell-nginx: ## Open shell in Nginx container
	podman-compose exec nginx /bin/bash

shell-orch: ## Open shell in Orch container
	podman-compose exec orch-service /bin/bash

purge: ## Remove all containers and images
	@echo -e "$(BLUE)Cleaning up containers, images, and volumes...$(NC)"
	podman-compose down --volumes --rmi all
	@echo -e "$(GREEN)Cleanup completed$(NC)"

clean-volumes: ## Remove all volumes
	@echo -e "$(BLUE)Cleaning up containers and volumes...$(NC)"
	podman-compose down --volumes
	@echo -e "$(GREEN)Volumes cleaned up$(NC)"

rebuild: purge build ## Force rebuild all images

dev: up ## Start development environment with full setup

# Development helpers
dev-logs: up logs ## Start dev environment and show logs

# Quick commands
quick-start: build up ## Quick start: build, start, and setup everything

# Maintenance
backup: ## Backup data volumes
	@echo -e "$(BLUE)Creating backup...$(NC)"
	@mkdir -p backups/$$(date +%Y%m%d_%H%M%S)
	@tar -czf backups/$$(date +%Y%m%d_%H%M%S)/data.tar.gz data/
	@echo -e "$(GREEN)Backup created in backups/$(NC)"

restore: ## Restore from backup (requires BACKUP_DIR)
	@if [ -z "$(BACKUP_DIR)" ]; then \
		echo -e "$(RED)Error: BACKUP_DIR not specified$(NC)"; \
		echo "Usage: make restore BACKUP_DIR=backups/YYYYMMDD_HHMMSS"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Restoring from $(BACKUP_DIR)...$(NC)"
	@tar -xzf $(BACKUP_DIR)/data.tar.gz
	@echo -e "$(GREEN)Restore completed$(NC)"

# Ansible Configuration Management
configure: ## Run Ansible configuration on existing Koji instance
	@echo -e "$(BLUE)Running Ansible configuration...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) --profile ansible up --build ansible-configurator
	@echo -e "$(GREEN)Ansible configuration completed$(NC)"

reconfigure: ## Force reconfiguration by restarting Ansible service
	@echo -e "$(BLUE)Force reconfiguring Koji with Ansible...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) --profile ansible rm -f ansible-configurator
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) --profile ansible up --build ansible-configurator
	@echo -e "$(GREEN)Ansible reconfiguration completed$(NC)"

logs-ansible: ## Show logs for Ansible Configurator
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) logs ansible-configurator

ansible-shell: ## Get shell access to ansible configurator (for debugging)
	@echo -e "$(BLUE)Starting interactive Ansible container...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) --profile ansible run --rm \
		--entrypoint /bin/bash ansible-configurator

validate-ansible: ## Validate Ansible configuration files
	@echo -e "$(BLUE)Validating Ansible configuration...$(NC)"
	@if [ ! -d "ansible-configs" ]; then \
		echo -e "$(RED)Error: ansible-configs directory not found$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Checking YAML syntax...$(NC)"
	@for file in ansible-configs/*.yml; do \
		if [ -f "$$file" ]; then \
			echo "Validating $$file..."; \
			python3 -c "import yaml; yaml.safe_load(open('$$file'))" || exit 1; \
		fi; \
	done
	@echo -e "$(GREEN)✓ All Ansible configuration files are valid$(NC)"


# The end.
