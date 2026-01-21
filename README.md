# SecVaultDemo
A security-focused personal secrets manager built to demonstrate application security best practices.

## Overview

SecureVault allows users to securely store and manage sensitive information (API keys, passwords, notes) with encryption at rest and a defense-in-depth security approach.

## Security Features

- **Authentication:** JWT-based auth with Argon2id password hashing
- **Encryption at Rest:** AES-256-GCM for all stored secrets
- **Input Validation:** Pydantic schemas with strict validation
- **SQL Injection Prevention:** SQLAlchemy ORM with parameterized queries
- **Security Headers:** Helmet-style middleware for HTTP security headers
- **Rate Limiting:** Protection against brute-force attacks
- **OWASP Top 10 Aligned:** See [SECURITY.md](docs/SECURITY.md) for details

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.12) |
| Frontend | React + TypeScript + Vite |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Containerization | Docker + Docker Compose |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Run Locally

```bash
# Clone the repository
git clone git@github.com:ghassenk/SecVaultDemo.git
cd SecVaultDemo

# Copy environment template
cp .env.example .env

# Start all services
docker compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Project Structure

```
securevault/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, security, encryption
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── main.py        # FastAPI application
│   ├── tests/             # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docker/
│   └── docker-compose.yml
├── .github/
│   └── workflows/         # CI/CD security pipeline
├── docs/
│   ├── SECURITY.md        # Security documentation
│   └── ARCHITECTURE.md    # Architecture details
└── README.md
```

## Security Pipeline

Every push and pull request triggers:

- 🔍 **Secrets Detection** - Gitleaks
- 🛡️ **SAST Backend** - Bandit + Semgrep
- 🛡️ **SAST Frontend** - ESLint security plugins
- 📦 **Dependency Scanning** - Trivy
- 🐳 **Container Scanning** - Trivy
- 📝 **Dockerfile Linting** - Hadolint

## Documentation

- [Security Documentation](docs/SECURITY.md) - Threat model and OWASP mapping
- [Architecture](docs/ARCHITECTURE.md) - Technical architecture details


## Development

### Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### Frontend
cd frontend
npm install
