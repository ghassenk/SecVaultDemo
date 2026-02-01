# ============================================
# SecureVault Frontend Dockerfile
# ============================================
# Security features:
# - Multi-stage build
# - Non-root user
# - Minimal production image with nginx
# - Security headers configured
# ============================================

# Build stage
FROM node:25-alpine AS builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Build the application
RUN npm run build


# Production stage
FROM nginx:alpine AS production

# Security: Add labels
LABEL org.opencontainers.image.title="SecureVault Frontend"
LABEL org.opencontainers.image.description="Security-focused secrets manager UI"
LABEL org.opencontainers.image.vendor="SecureVault"
LABEL org.opencontainers.image.version="1.0.0"

# Security: Remove default nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy built application
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy nginx configuration with security headers
COPY nginx.conf /etc/nginx/nginx.conf

# Security: Create non-root user and set permissions
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser && \
    chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appgroup /var/run/nginx.pid

# Security: Switch to non-root user
USER appuser

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1

CMD ["nginx", "-g", "daemon off;"]
