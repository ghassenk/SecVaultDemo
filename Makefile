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

# Start services in background
dev-bg:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Clean up (stop containers, remove volumes)
clean:
	docker compose down -v
