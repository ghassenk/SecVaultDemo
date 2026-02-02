# SecVaultDemo Security Documentation

## Security Overview

SecVaultDemo implements defense-in-depth security following OWASP guidelines. This document details the security measures, threat model, and mitigations.

## OWASP Top 10 Mapping

| OWASP Category | Status | Implementation |
|----------------|--------|----------------|
| A01: Broken Access Control | ✅ | Row-level authorization, JWT validation |
| A02: Cryptographic Failures | ✅ | AES-256-GCM, Argon2id, TLS |
| A03: Injection | ✅ | SQLAlchemy ORM, Pydantic validation |
| A04: Insecure Design | ✅ | Threat modeling, secure defaults |
| A05: Security Misconfiguration | ✅ | Hardened containers, security headers |
| A06: Vulnerable Components | ✅ | Dependabot, Trivy scanning |
| A07: Auth Failures | ✅ | Rate limiting, strong passwords |
| A08: Data Integrity Failures | ✅ | Input validation, HMAC in GCM |
| A09: Logging Failures | ⚠️ | Basic logging (enhance for prod) |
| A10: SSRF | ✅ | No user-controlled URLs |

## Authentication

### Password Security

**Algorithm:** Argon2id (winner of Password Hashing Competition)

```python
Parameters:
- Memory: 65,536 KB (64 MB)
- Iterations: 3
- Parallelism: 4
- Salt: 16 bytes random
- Hash length: 32 bytes
```

**Password Requirements:**
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### JWT Tokens

| Token Type | Lifetime | Purpose |
|------------|----------|---------|
| Access Token | 15 minutes | API authentication |
| Refresh Token | 7 days | Obtain new access tokens |

**Security measures:**
- Signed with HS256 (HMAC-SHA256)
- Contains: user_id, email, expiration, type
- Stored in memory only (frontend)
- Refresh tokens are single-use (recommended enhancement)

### Rate Limiting

- 100 requests per minute per IP
- Login endpoint: 5 attempts per minute
- Implemented via slowapi middleware

## Encryption

### Secrets at Rest

**Algorithm:** AES-256-GCM (Authenticated Encryption)

```
┌─────────────────────────────────────────────────────┐
│                  Encryption Flow                     │
├─────────────────────────────────────────────────────┤
│  MASTER_KEY (env var, 256-bit)                      │
│       │                                             │
│       ▼                                             │
│  HKDF(master_key, user_id) → per_user_key          │
│       │                                             │
│       ▼                                             │
│  AES-256-GCM(per_user_key, nonce, plaintext)       │
│       │                                             │
│       ▼                                             │
│  ciphertext + auth_tag (stored in DB)              │
└─────────────────────────────────────────────────────┘
```

**Key points:**
- Each user has a derived key (key separation)
- Each encryption uses a unique 12-byte nonce
- GCM provides authentication (tamper detection)
- Master key never stored in database

### Key Management

| Key | Storage | Rotation |
|-----|---------|----------|
| Master Encryption Key | Environment variable | Manual (requires re-encryption) |
| JWT Secret | Environment variable | Can rotate (invalidates sessions) |
| Database Password | Environment variable | Can rotate |

## HTTP Security Headers

```python
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; ...",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"  # Production only
}
```

## Container Security

### Hardening Measures

1. **Non-root users** - All containers run as unprivileged users
2. **Read-only filesystem** - Where possible, with tmpfs for needed writes
3. **Resource limits** - CPU and memory constraints
4. **No new privileges** - `security_opt: no-new-privileges:true`
5. **Minimal images** - Python slim, nginx alpine
6. **Network isolation** - Database not exposed externally

### Dockerfile Security

```dockerfile
# Multi-stage build (smaller attack surface)
FROM python:3.12-slim AS builder
# ... build dependencies ...

FROM python:3.12-slim AS production
# Non-root user
RUN useradd --uid 1000 appuser
USER appuser
```

## CI/CD Security

### Secret Detection

- **Pre-commit hook:** Gitleaks runs locally before each commit
- **CI pipeline:** Gitleaks scans full git history
- **GitHub:** Secret scanning enabled on repository

### Dependency Scanning

| Tool | Target | Frequency |
|------|--------|-----------|
| Dependabot | All dependencies | Weekly PRs |
| pip-audit | Python packages | Every push |
| npm audit | Node packages | Every push |
| Trivy | Containers + deps | Every push |

### SAST (Static Analysis)

- **Bandit:** Python security linter
- **ESLint:** JavaScript/TypeScript with security plugins
- **Hadolint:** Dockerfile best practices

## AWS/Infrastructure Security

### OIDC Authentication

GitHub Actions authenticates to AWS without stored credentials:

```
GitHub Action → AWS STS → Assume Role → Temporary Credentials (1 hour)
```

**IAM Policy:** Minimal Lightsail permissions only
- Cannot access other AWS services
- Region-restricted
- Branch-restricted (main only)

### Network Security

```
Internet → Nginx (80/443) → Backend (internal) → PostgreSQL (internal)
                                                        │
                                              Not exposed externally
```

## Threat Model

### Assets

1. User credentials (passwords)
2. Stored secrets (API keys, passwords, etc.)
3. JWT tokens
4. Master encryption key

### Threat Actors

1. **External attackers** - Internet-based attacks
2. **Malicious users** - Authenticated but unauthorized access
3. **Insider threats** - Access to infrastructure

### Attack Vectors & Mitigations

| Attack | Mitigation |
|--------|------------|
| Brute force login | Rate limiting, strong password policy |
| SQL injection | ORM with parameterized queries |
| XSS | CSP headers, React auto-escaping |
| CSRF | SameSite cookies, no cookie auth |
| Token theft | Memory-only storage, short expiry |
| Database breach | Encryption at rest, per-user keys |
| Man-in-the-middle | TLS, HSTS |
| Container escape | Non-root, read-only, no privileges |

## Security Checklist for Production

- [ ] Generate new secrets (JWT, encryption key, DB password)
- [ ] Enable HTTPS with valid certificate
- [ ] Set `ENVIRONMENT=production`
- [ ] Restrict SSH access to specific IPs
- [ ] Enable AWS CloudTrail logging
- [ ] Set up monitoring/alerting
- [ ] Configure backup for PostgreSQL
- [ ] Review and restrict IAM permissions
- [ ] Enable GitHub branch protection
- [ ] Test disaster recovery procedure
