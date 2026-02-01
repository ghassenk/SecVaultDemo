#!/bin/bash
set -e

# Log output for debugging
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting SecVault setup at $(date)"

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install additional tools
apt-get install -y git make certbot python3-certbot-nginx nginx

# Clone repository
APP_DIR="${app_dir}"
mkdir -p $APP_DIR
git clone "${repo_url}" $APP_DIR || echo "Clone failed - will need manual clone"
chown -R ubuntu:ubuntu $APP_DIR

# Create .env template if repo was cloned
if [ -d "$APP_DIR" ]; then
  cd $APP_DIR

  # Generate .env from template if it exists
  if [ -f "env.production.example" ]; then
    cp env.production.example .env

    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)

    # Replace placeholders in .env
    sed -i "s/your-super-secret-key-change-in-production-min-32-chars/$SECRET_KEY/" .env
    sed -i "s/your-32-byte-hex-encryption-key-here-change-me-now/$ENCRYPTION_KEY/" .env
    sed -i "s/strong_production_password_here/$DB_PASSWORD/" .env

    echo "Generated .env with random secrets"
  fi
fi

# Setup nginx as reverse proxy (basic config, will be updated by certbot for SSL)
%{ if domain_name != "" }
cat > /etc/nginx/sites-available/secvault << 'NGINX'
server {
    listen 80;
    server_name ${domain_name};

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/secvault /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl reload nginx
%{ endif }

# Create systemd service for auto-start
cat > /etc/systemd/system/secvault.service << 'SERVICE'
[Unit]
Description=SecVault Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${app_dir}
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable secvault.service

echo "SecVault setup completed at $(date)"
echo "NOTE: SSH in and run 'sudo make prod-build' in $APP_DIR to start the application"
