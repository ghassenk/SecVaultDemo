# Make sure DB is running
```docker compose up db -d```

# Set env vars

`export JWT_SECRET_KEY=$(openssl rand -hex 32)`
`export ENCRYPTION_MASTER_KEY=$(openssl rand -hex 32)`
`export DATABASE_URL=postgresql+asyncpg://securevault:securevault_dev_password@localhost:5432/securevault`


# Run tests
`ENVIRONMENT=testing pytest -v`
