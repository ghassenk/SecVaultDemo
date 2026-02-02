# SecVaultDemo Architecture

## Overview

SecVaultDemo is a full-stack secrets management application demonstrating security best practices. It uses a React frontend, FastAPI backend, and PostgreSQL database.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Nginx (Reverse Proxy)                       │
│              - SSL termination (production)                     │
│              - Security headers (CSP, HSTS, etc.)               │
│              - Static file serving                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    │
┌─────────────────┐  ┌─────────────────┐          │
│  React Frontend │  │  FastAPI Backend │          │
│  (Static Files) │  │   /api/v1/*     │          │
│  Port 8080      │  │   Port 8000     │          │
└─────────────────┘  └────────┬────────┘          │
                              │                    │
                              ▼                    │
                     ┌─────────────────┐          │
                     │   PostgreSQL    │          │
                     │   Port 5432     │          │
                     │   (Internal)    │          │
                     └─────────────────┘          │
                                                  │
└─────────────────── Docker Network ──────────────┘
```

## Component Details

### Frontend (React + TypeScript + Vite)

```
frontend/src/
├── api/
│   └── client.ts          # HTTP client with token management
├── contexts/
│   └── AuthContext.tsx    # Authentication state (tokens in memory)
├── pages/
│   ├── LoginPage.tsx      # Login form
│   ├── RegisterPage.tsx   # Registration with password strength
│   └── SecretsPage.tsx    # CRUD for secrets
├── components/
│   ├── SecretModal.tsx    # Create/Edit secret modal
│   └── ConfirmModal.tsx   # Delete confirmation
├── types/
│   └── index.ts           # TypeScript interfaces
└── App.tsx                # Router setup
```

**Key Security Decisions:**
- Tokens stored in memory only (not localStorage)
- Auto-refresh on 401 responses
- Password strength indicator during registration

### Backend (FastAPI + SQLAlchemy)

```
backend/app/
├── api/
│   ├── auth.py            # Authentication endpoints
│   ├── secrets.py         # Secrets CRUD endpoints
│   └── health.py          # Health check
├── core/
│   ├── config.py          # Pydantic settings
│   ├── database.py        # Async SQLAlchemy setup
│   ├── jwt.py             # Token creation/validation
│   ├── password.py        # Argon2id hashing
│   ├── encryption.py      # AES-256-GCM encryption
│   └── security.py        # CORS, headers, rate limiting
├── models/
│   ├── user.py            # User SQLAlchemy model
│   └── secret.py          # Secret SQLAlchemy model
└── schemas/
    ├── auth.py            # Auth request/response schemas
    ├── user.py            # User schemas
    └── secret.py          # Secret schemas
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Secrets table
CREATE TABLE secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    encrypted_value BYTEA NOT NULL,  -- AES-256-GCM encrypted
    nonce BYTEA NOT NULL,            -- 12-byte unique nonce
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

## Data Flow

### Authentication Flow

```
1. Register: POST /api/v1/auth/register
   └─> Validate password strength
   └─> Hash with Argon2id
   └─> Store user in DB

2. Login: POST /api/v1/auth/login
   └─> Verify credentials
   └─> Generate JWT access token (15min)
   └─> Generate JWT refresh token (7 days)
   └─> Return tokens

3. Refresh: POST /api/v1/auth/refresh
   └─> Validate refresh token
   └─> Issue new access token
```

### Secret Encryption Flow

```
Create Secret:
1. Receive plaintext from user
2. Derive per-user key: HKDF(master_key, user_id)
3. Generate random 12-byte nonce
4. Encrypt: AES-256-GCM(derived_key, nonce, plaintext)
5. Store: encrypted_value + nonce in DB

Read Secret:
1. Fetch encrypted_value + nonce from DB
2. Derive same per-user key
3. Decrypt: AES-256-GCM(derived_key, nonce, ciphertext)
4. Return plaintext
```

## Infrastructure

### Docker Compose (Development)

- Hot reload for frontend and backend
- PostgreSQL with persistent volume
- All services on same network

### Docker Compose (Production)

- Internal network for backend/db (not exposed)
- Read-only filesystems where possible
- Resource limits (CPU/memory)
- Non-root container users
- Security headers via nginx

### Terraform (AWS Lightsail)

- Single instance deployment
- Static IP for DNS
- Automated provisioning via GitHub Actions
- OIDC authentication (no stored AWS keys)

## CI/CD Pipeline

```
Push to main
    │
    ├─> Security Scanning
    │   ├── Gitleaks (secrets)
    │   ├── Bandit (Python SAST)
    │   ├── Trivy (dependencies)
    │   └── Hadolint (Dockerfile)
    │
    ├─> Unit Tests
    │   ├── Backend (pytest + PostgreSQL)
    │   └── Frontend (vitest smoke test)
    │
    └─> Deploy (manual trigger)
        └── Terraform → AWS Lightsail
```
