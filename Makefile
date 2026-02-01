.PHONY: setup env dev clean

# Generate .env file with random secrets
env:
	@if [ -f .env ]; then \
		echo "⚠️  .env already exists. Remove it first or run 'make env-force'"; \
	else \
		echo "Creating .env with generated secrets..."; \
		sed -e "s/CHANGE_ME_generate_jwt_secret_key/$$(openssl rand -hex 32)/" \
		    -e "s/CHANGE_ME_generate_encryption_master_key/$$(openssl rand -hex 32)/" \
		    env.example > .env; \
		echo "✅ .env created successfully"; \
	fi

# Force regenerate .env (overwrites existing)
env-force:
	@echo "Creating .env with generated secrets..."
	@sed -e "s/CHANGE_ME_generate_jwt_secret_key/$$(openssl rand -hex 32)/" \
	     -e "s/CHANGE_ME_generate_encryption_master_key/$$(openssl rand -hex 32)/" \
	     env.example > .env
	@echo "✅ .env created successfully"

# Start all services
dev:
	docker compose up

# Start with rebuild (use after code changes)
dev-build:
	docker compose up --build

# Start services in background
dev-bg:
	docker compose up -d

# Rebuild and start in background
dev-build-bg:
	docker compose up --build -d

# Stop all services
down:
	docker compose down

# Clean up (stop containers, remove volumes)
clean:
	docker compose down -v

# ============================================
# Production Commands
# ============================================

# Start production stack
prod:
	docker compose -f docker-compose.prod.yml up -d

# Build and start production
prod-build:
	docker compose -f docker-compose.prod.yml up --build -d

# Stop production
prod-down:
	docker compose -f docker-compose.prod.yml down

# View logs
logs:
	docker compose logs -f

logs-prod:
	docker compose -f docker-compose.prod.yml logs -f

# Check status
status:
	docker compose ps

status-prod:
	docker compose -f docker-compose.prod.yml ps
