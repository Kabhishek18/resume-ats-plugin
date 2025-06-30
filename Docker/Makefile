# Docker/Makefile - Docker management commands

.PHONY: help build up down restart logs clean test deploy

# Default target
help:	## Show this help
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build:	## Build all Docker images
	@echo "🔨 Building Docker images..."
	docker-compose -f docker-compose.yml build --no-cache

build-fast:	## Build Docker images (with cache)
	@echo "🔨 Building Docker images (fast)..."
	docker-compose -f docker-compose.yml build

up:	## Start all services
	@echo "🚀 Starting ATS Resume Scorer services..."
	docker-compose -f docker-compose.yml up -d
	@echo "✅ Services started!"
	@echo "📱 Web API: http://localhost:8000"
	@echo "📊 Grafana: http://localhost:3000 (admin/admin123)"
	@echo "🔍 Prometheus: http://localhost:9090"

up-api-only:	## Start only the API service
	@echo "🚀 Starting API service only..."
	docker-compose -f docker-compose.yml up -d ats-scorer-api redis postgres

up-dev:	## Start services in development mode
	@echo "🛠️  Starting in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:	## Stop all services
	@echo "🛑 Stopping services..."
	docker-compose -f docker-compose.yml down

down-volumes:	## Stop services and remove volumes
	@echo "🛑 Stopping services and removing volumes..."
	docker-compose -f docker-compose.yml down -v

restart:	## Restart all services
	@echo "🔄 Restarting services..."
	docker-compose -f docker-compose.yml restart

restart-api:	## Restart only API service
	@echo "🔄 Restarting API service..."
	docker-compose -f docker-compose.yml restart ats-scorer-api

logs:	## Show logs for all services
	docker-compose -f docker-compose.yml logs -f

logs-api:	## Show logs for API service
	docker-compose -f docker-compose.yml logs -f ats-scorer-api

logs-db:	## Show database logs
	docker-compose -f docker-compose.yml logs -f postgres

status:	## Show service status
	@echo "📊 Service Status:"
	docker-compose -f docker-compose.yml ps

health:	## Check health of all services
	@echo "🏥 Health Check:"
	@docker-compose -f docker-compose.yml ps --services | xargs -I {} sh -c 'echo "Checking {}: $$(docker-compose -f docker-compose.yml exec -T {} curl -f http://localhost:8000/health 2>/dev/null || echo "Not accessible")"'

clean:	## Clean up containers, images, and volumes
	@echo "🧹 Cleaning up..."
	docker-compose -f docker-compose.yml down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

clean-all:	## Clean everything including images
	@echo "🧹 Deep cleaning..."
	docker-compose -f docker-compose.yml down -v --remove-orphans --rmi all
	docker system prune -a -f
	docker volume prune -f

test:	## Run tests in Docker
	@echo "🧪 Running tests..."
	docker-compose -f docker-compose.yml exec ats-scorer-cli python -m pytest tests/ -v

test-build:	## Build and run tests
	@echo "🧪 Building and running tests..."
	docker-compose -f docker-compose.yml up -d --build ats-scorer-cli
	docker-compose -f docker-compose.yml exec ats-scorer-cli python -m pytest tests/ -v

shell:	## Open shell in CLI container
	@echo "🐚 Opening shell..."
	docker-compose -f docker-compose.yml exec ats-scorer-cli /bin/bash

shell-api:	## Open shell in API container
	@echo "🐚 Opening API shell..."
	docker-compose -f docker-compose.yml exec ats-scorer-api /bin/bash

db-shell:	## Open PostgreSQL shell
	@echo "🗄️  Opening database shell..."
	docker-compose -f docker-compose.yml exec postgres psql -U ats_user -d ats_scorer

redis-shell:	## Open Redis shell
	@echo "📦 Opening Redis shell..."
	docker-compose -f docker-compose.yml exec redis redis-cli

backup-db:	## Backup database
	@echo "💾 Backing up database..."
	mkdir -p backups
	docker-compose -f docker-compose.yml exec postgres pg_dump -U ats_user ats_scorer > backups/ats_scorer_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up to backups/"

restore-db:	## Restore database (set BACKUP_FILE=filename)
	@echo "📥 Restoring database from $(BACKUP_FILE)..."
	@if [ -z "$(BACKUP_FILE)" ]; then echo "❌ Please set BACKUP_FILE=filename"; exit 1; fi
	docker-compose -f docker-compose.yml exec -T postgres psql -U ats_user ats_scorer < $(BACKUP_FILE)
	@echo "✅ Database restored"

score-example:	## Score example resume
	@echo "📄 Scoring example resume..."
	docker-compose -f docker-compose.yml exec ats-scorer-cli python -m ats_resume_scorer.main \
		--resume examples/sample_resume.pdf \
		--jd examples/sample_jd.txt

batch-example:	## Run batch scoring example
	@echo "📁 Running batch scoring..."
	docker-compose -f docker-compose.yml exec ats-scorer-cli python cli_advanced.py batch \
		--resume-dir examples/resumes \
		--jd examples/sample_jd.txt \
		--output output/batch_results.csv

deploy-prod:	## Deploy to production
	@echo "🚀 Deploying to production..."
	@echo "⚠️  Make sure you have set production environment variables!"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

monitor:	## Show real-time resource usage
	@echo "📊 Resource Monitor (Press Ctrl+C to exit):"
	watch docker stats

install-deps:	## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

update:	## Update and rebuild services
	@echo "🔄 Updating services..."
	git pull
	docker-compose -f docker-compose.yml build --no-cache
	docker-compose -f docker-compose.yml up -d

# Development helpers
dev-setup:	## Setup development environment
	@echo "🛠️  Setting up development environment..."
	make install-deps
	make build
	make up-dev
	@echo "✅ Development environment ready!"

# Production helpers  
prod-check:	## Check production readiness
	@echo "✅ Production Readiness Check:"
	@echo "  - Docker version: $$(docker --version)"
	@echo "  - Docker Compose version: $$(docker-compose --version)"
	@echo "  - Available disk space: $$(df -h / | awk 'NR==2{print $$4}')"
	@echo "  - Available memory: $$(free -h | awk 'NR==2{print $$7}')"
	@echo "  - Environment variables check:"
	@env | grep -E "(POSTGRES_|REDIS_|LOG_)" || echo "    No production env vars set"

# Utility targets
show-urls:	## Show all service URLs
	@echo "🌐 Service URLs:"
	@echo "  Main API:    http://localhost:8000"
	@echo "  API Docs:    http://localhost:8000/docs"
	@echo "  Health:      http://localhost:8000/health"
	@echo "  Grafana:     http://localhost:3000"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Database:    localhost:5432"
	@echo "  Redis:       localhost:6379"