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
	@echo -e "  BUILD_ARCH       - Target architecture (default: x86_64)"
	@echo -e "  COMPOSE_FILE     - Docker compose file (default: docker-compose.yml)"

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
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) build --no-cache
	@echo -e "$(GREEN)All images built successfully$(NC)"

build-fast: pull-koji ## Build all container images (cached)
	@echo -e "$(BLUE)Building all container images (using cache)...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) build
	@echo -e "$(GREEN)All images built successfully$(NC)"

up: ## Start all services
	@echo -e "$(BLUE)Starting Koji environment...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) up -d
	@echo -e "$(YELLOW)Waiting for services to be ready...$(NC)"
	@sleep 10
	@echo -e "$(GREEN)Koji environment started$(NC)"
	@echo -e "$(BLUE)Services available at:$(NC)"
	@echo -e "  Koji Hub:     http://localhost:8080"
	@echo -e "  Koji Web:     http://localhost:8081"
	@echo -e "  Storage:      http://localhost:8082"

launch:
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) up --build

relaunch: down launch ## Restart all services

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

status: ## Show status of all services
	@echo -e "$(BLUE)Service Status:$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) ps

setup-db: ## Initialize database schema
	@echo -e "$(BLUE)Setting up database...$(NC)"
	@if [ ! -f "data/postgres/.initialized" ]; then \
		echo -e "$(YELLOW)Initializing database schema...$(NC)"; \
		podman exec koji-boxed-postgres-1 psql -U koji -d koji -f /docker-entrypoint-initdb.d/init-koji.sql; \
		touch data/postgres/.initialized; \
		echo -e "$(GREEN)Database initialized$(NC)"; \
	else \
		echo -e "$(YELLOW)Database already initialized$(NC)"; \
	fi

setup-hub: ## Configure Koji Hub
	@echo -e "$(BLUE)Configuring Koji Hub...$(NC)"
	@if [ ! -f "data/koji-storage/.hub-configured" ]; then \
		echo -e "$(YELLOW)Running hub setup...$(NC)"; \
		podman exec koji-boxed-koji-hub-1 /usr/local/bin/setup-koji-hub.sh; \
		touch data/koji-storage/.hub-configured; \
		echo -e "$(GREEN)Hub configured$(NC)"; \
	else \
		echo -e "$(YELLOW)Hub already configured$(NC)"; \
	fi

setup: setup-db setup-hub ## Complete environment setup

setup-kdc: ## Setup KDC and create service principals
	@echo -e "$(BLUE)Setting up KDC...$(NC)"
	@if [ ! -f "data/kdc/.initialized" ]; then \
		echo -e "$(YELLOW)Initializing KDC realm...$(NC)"; \
		podman exec koji-boxed-kdc-1 /usr/local/bin/setup-kdc.sh; \
		touch data/kdc/.initialized; \
		echo -e "$(GREEN)KDC initialized$(NC)"; \
	else \
		echo -e "$(YELLOW)KDC already initialized$(NC)"; \
	fi

kinit-admin: ## Get Kerberos ticket for admin user
	@echo -e "$(BLUE)Getting Kerberos ticket for admin...$(NC)"
	podman exec koji-boxed-kdc-1 kinit admin/admin@KOJI.BOX -w admin_password

list-principals: ## List Kerberos principals
	@echo -e "$(BLUE)Listing Kerberos principals...$(NC)"
	podman exec koji-boxed-kdc-1 kadmin.local -q "list_principals"

test-kerberos: ## Test Kerberos authentication
	@echo -e "$(BLUE)Testing Kerberos authentication...$(NC)"
	podman exec koji-boxed-kdc-1 kinit admin/admin@KOJI.BOX -w admin_password
	podman exec koji-boxed-kdc-1 klist

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

shell-hub: ## Open shell in Koji Hub container
	podman exec -it koji-boxed-koji-hub-1 /bin/bash

shell-worker: ## Open shell in Koji Worker container
	podman exec -it koji-boxed-koji-worker-1 /bin/bash

shell-web: ## Open shell in Koji Web container
	podman exec -it koji-boxed-koji-web-1 /bin/bash

shell-postgres: ## Open shell in PostgreSQL container
	podman exec -it koji-boxed-postgres-1 /bin/bash

shell-kdc: ## Open shell in KDC container
	podman exec -it koji-boxed-kdc-1 /bin/bash

shell-nginx: ## Open shell in Nginx container
	podman exec -it koji-boxed-nginx-1 /bin/bash

clean: ## Remove all containers and images
	@echo -e "$(BLUE)Cleaning up...$(NC)"
	podman-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME) down -v --rmi all
	podman system prune -f
	@echo -e "$(GREEN)Cleanup completed$(NC)"

clean-data: ## Remove all data volumes
	@echo -e "$(BLUE)Removing data volumes...$(NC)"
	rm -rf data/postgres/*
	rm -rf data/koji-storage/*
	rm -rf data/logs/*
	@echo -e "$(GREEN)Data volumes cleaned$(NC)"

rebuild: clean build ## Force rebuild all images

dev: up setup ## Start development environment with full setup

# Development helpers
dev-logs: up setup logs ## Start dev environment and show logs

# Quick commands
quick-start: build up setup ## Quick start: build, start, and setup everything

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
