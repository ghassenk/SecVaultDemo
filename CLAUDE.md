# SecureVault - Project Context

## Overview
SecureVault is a security-focused personal secrets manager demonstrating application security best practices. Built as a full-stack demo with FastAPI backend and React frontend.

## Current Status

### ✅ Completed

**Phase 1-3: Project Scaffolding & Auth**
- FastAPI backend structure with proper separation (api/, core/, models/, schemas/)
- PostgreSQL with async SQLAlchemy
- User authentication with Argon2id password hashing
- JWT tokens (access + refresh) with proper expiration
- Password strength validation (12+ chars, mixed case, digits, special chars)
- Health endpoint at `/api/v1/health`

**Phase 4: Secrets CRUD with Encryption**
- AES-256-GCM authenticated encryption
- Per-user key derivation via HKDF (master key + user_id)
- Unique 12-byte nonce per encryption operation
- Full CRUD: create, read, update, delete secrets
- Row-level authorization (users only see their own secrets)
- 404 returned for both non-existent and unauthorized (no info leakage)

### 🔲 Next Up

**Phase 5: React Frontend**
- Login/Register forms
- Secrets list view (paginated)
- Create/Edit/Delete secret modals
- Secure token handling (memory only, NOT localStorage)
- Proper logout with token clearing

**Phase 6: Docker Compose Integration**
- Full stack deployment
- Environment configuration
- Production hardening

## Architecture

```
securevault/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   │   ├── auth.py    # /register, /login, /refresh, /me, /change-password
│   │   │   ├── secrets.py # CRUD for secrets
│   │   │   └── health.py
│   │   ├── core/          # Business logic
│   │   │   ├── config.py  # Pydantic settings
│   │   │   ├── database.py
│   │   │   ├── security.py    # CORS, rate limiting, security headers
│   │   │   ├── jwt.py         # Token creation/validation
│   │   │   ├── password.py    # Argon2id hashing
│   │   │   └── encryption.py  # AES-256-GCM
│   │   ├── models/        # SQLAlchemy models (User, Secret)
│   │   └── schemas/       # Pydantic schemas
│   └── tests/
├── frontend/              # React + Vite + TypeScript (scaffolded, not built)
├── docker-compose.yml
└── docs/
    ├── ARCHITECTURE.md
    └── SECURITY.md
```

## Key Security Decisions

1. **Passwords**: Argon2id with memory=65536KB, iterations=3, parallelism=4
2. **Tokens**: JWT with 15min access / 7day refresh, signed with HS256
3. **Encryption**: AES-256-GCM with HKDF-derived per-user keys
4. **Headers**: X-Frame-Options, CSP, HSTS (in prod), X-Content-Type-Options
5. **Auth**: Bearer tokens, never stored in localStorage (frontend should use memory)

## API Endpoints

```
POST   /api/v1/auth/register       # Create account
POST   /api/v1/auth/login          # Get tokens
POST   /api/v1/auth/refresh        # Refresh access token
GET    /api/v1/auth/me             # Get current user
POST   /api/v1/auth/change-password

GET    /api/v1/secrets             # List (paginated, metadata only)
POST   /api/v1/secrets             # Create
GET    /api/v1/secrets/{id}        # Get with decrypted content
PUT    /api/v1/secrets/{id}        # Update
DELETE /api/v1/secrets/{id}        # Delete

GET    /api/v1/health              # Health check
```

## Running the Project

```bash
# Start database
docker compose up db -d

# Backend (from backend/)
pip install -r requirements.txt
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export ENCRYPTION_MASTER_KEY=$(openssl rand -hex 32)
export DATABASE_URL=postgresql+asyncpg://securevault:securevault_dev_password@localhost:5432/securevault
uvicorn app.main:app --reload

# Tests
make test  # or see Makefile for options
```

## Environment Variables

Required:
- `JWT_SECRET_KEY` - 256-bit hex string for JWT signing
- `ENCRYPTION_MASTER_KEY` - 256-bit hex string for AES encryption
- `DATABASE_URL` - PostgreSQL connection string

Optional:
- `ENVIRONMENT` - development/staging/production/testing
- `DEBUG` - true/false

## Notes for Phase 5 (Frontend)

The frontend scaffold exists but needs implementation:
- Use React + TypeScript + Vite (already configured)
- Store tokens in memory (React state/context), NOT localStorage
- Implement token refresh logic before expiration
- Use httpOnly cookies if you want persistence (requires backend changes)
- Tailwind CSS is available for styling
