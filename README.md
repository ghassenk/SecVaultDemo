# SecVaultDemo

A security-focused personal secrets manager demonstrating application security best practices.

## Features

- 🔐 **Secure Authentication** - JWT tokens with Argon2id password hashing
- 🔒 **Encryption at Rest** - AES-256-GCM with per-user key derivation (HKDF)
- 🛡️ **Defense in Depth** - Security headers, input validation, rate limiting
- 🐳 **Production Ready** - Docker Compose with network isolation, resource limits
- 🚀 **CI/CD** - GitHub Actions with security scanning, Terraform deployment

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.12) |
| Frontend | React 18 + TypeScript + Vite |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Infrastructure | Docker, Terraform, AWS Lightsail |

## Quick Start

```bash
# Clone and setup
git clone git@github.com:ghassenk/SecVaultDemo.git
cd SecVaultDemo

# Generate .env with random secrets
make env

# Start all services
make dev-build

# Access
# Frontend: http://localhost:8080
# Backend API: http://localhost:8000/docs
```

## Project Structure

```
SecVaultDemo/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers (auth, secrets, health)
│   │   ├── core/          # Config, security, JWT, encryption
│   │   ├── models/        # SQLAlchemy models
│   │   └── schemas/       # Pydantic schemas
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/           # API client with token management
│   │   ├── contexts/      # Auth context (tokens in memory)
│   │   ├── pages/         # Login, Register, Secrets
│   │   └── components/    # Modals, forms
│   └── Dockerfile
├── terraform/             # AWS Lightsail IaC
├── .github/workflows/     # CI/CD pipelines
├── docker-compose.yml     # Development
└── docker-compose.prod.yml # Production
```

## API Endpoints

```
POST   /api/v1/auth/register        # Create account
POST   /api/v1/auth/login           # Get tokens
POST   /api/v1/auth/refresh         # Refresh access token
POST   /api/v1/auth/logout          # Invalidate session
GET    /api/v1/auth/me              # Current user
POST   /api/v1/auth/change-password # Change password

GET    /api/v1/secrets              # List (paginated)
POST   /api/v1/secrets              # Create
GET    /api/v1/secrets/{id}         # Get (decrypted)
PUT    /api/v1/secrets/{id}         # Update
DELETE /api/v1/secrets/{id}         # Delete

GET    /api/v1/health               # Health check
```

## Security

| Layer | Implementation |
|-------|----------------|
| Passwords | Argon2id (65MB memory, 3 iterations) |
| Tokens | JWT HS256, 15min access / 7d refresh |
| Encryption | AES-256-GCM + HKDF per-user keys |
| Headers | CSP, X-Frame-Options, HSTS |
| Frontend | Tokens in memory only (not localStorage) |

See [docs/SECURITY.md](docs/SECURITY.md) for threat model and OWASP mapping.

## CI/CD Pipeline

Every push triggers:
- 🔍 **Gitleaks** - Secret detection
- 🛡️ **Bandit** - Python security analysis
- 📦 **Trivy** - Dependency & container scanning
- 🐳 **Hadolint** - Dockerfile linting
- ✅ **Pytest** - Unit tests

Deployment via Terraform to AWS Lightsail with OIDC authentication (no stored credentials).

## Development

```bash
# Backend only
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
make test

# Frontend only
cd frontend
npm install
npm run dev

# Full stack
make dev          # Start all containers
make dev-build    # Rebuild and start
make prod-build   # Production build
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | 256-bit hex for JWT signing |
| `ENCRYPTION_MASTER_KEY` | 256-bit hex for AES encryption |
| `POSTGRES_PASSWORD` | Database password |
| `ENVIRONMENT` | development / production |

Generate with: `make env`

## Documentation

- [Security Documentation](docs/SECURITY.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Testing Guide](backend/doc/API_TESTING.md)
