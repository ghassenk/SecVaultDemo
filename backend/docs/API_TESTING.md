# Auth
## Register
```
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecureP@ssw0rd!"}'
```

## Login
```
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecureP@ssw0rd!"}'
```

# Secret
## Create secret
```
curl -X POST http://localhost:8000/api/v1/secrets \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"AWS Key","content":"AKIAIOSFODNN7EXAMPLE"}'
```

## List secrets
```
curl http://localhost:8000/api/v1/secrets \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Get secret (decrypted)
```
curl http://localhost:8000/api/v1/secrets/SECRET_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
  ```
