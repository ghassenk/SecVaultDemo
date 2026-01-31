# Makefile
.PHONY: test test-cov lint

# Default: run all tests
test:
	docker compose up db -d
	JWT_SECRET_KEY=$$(openssl rand -hex 32) \
	ENCRYPTION_MASTER_KEY=$$(openssl rand -hex 32) \
	ENVIRONMENT=testing \
	DATABASE_URL=postgresql+asyncpg://securevault:securevault_dev_password@localhost:5432/securevault \
	pytest $(ARGS)

test-cov:
	docker compose up db -d
	JWT_SECRET_KEY=$$(openssl rand -hex 32) \
	ENCRYPTION_MASTER_KEY=$$(openssl rand -hex 32) \
	ENVIRONMENT=testing \
	DATABASE_URL=postgresql+asyncpg://securevault:securevault_dev_password@localhost:5432/securevault \
	coverage run --concurrency=greenlet,thread -m pytest && coverage report --show-missing && coverage html

lint:
	ruff check app tests