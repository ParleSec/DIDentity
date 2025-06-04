#!/bin/sh

# Service Configuration Script
# Creates basic configuration files using fixed passwords from Vault

set -e

export VAULT_ADDR=http://vault:8200
export VAULT_TOKEN=root

echo "Configuring services with fixed Vault secrets..."

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
until vault status > /dev/null 2>&1; do
    echo "Vault not ready, waiting..."
    sleep 2
done

echo "Vault is ready. Using fixed passwords..."

# Fixed passwords (matching Vault and container configuration)
DB_PASSWORD="VaultSecureDB2024"
RABBITMQ_PASSWORD="VaultSecureRMQ2024"
GRAFANA_ADMIN_PASSWORD="VaultSecureGrafana2024"
JWT_SECRET_KEY="VaultJWTSecret2024SuperSecure"

# Create basic environment file for reference
cat > /tmp/vault-secrets.env << EOF
# Fixed passwords for DIDentity system
POSTGRES_PASSWORD=${DB_PASSWORD}
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/decentralized_id
RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
RABBITMQ_URL=amqp://admin:${RABBITMQ_PASSWORD}@rabbitmq:5672/
GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=root
EOF

echo "✓ Basic environment configuration created at /tmp/vault-secrets.env"

# Create minimal service configurations directory
mkdir -p /tmp/service-configs

# Create a simple service environment template
cat > /tmp/service-configs/service-template.env << EOF
# Standard service configuration
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/decentralized_id
RABBITMQ_URL=amqp://admin:${RABBITMQ_PASSWORD}@rabbitmq:5672/
JWT_SECRET_KEY=${JWT_SECRET_KEY}
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=root
OTLP_ENDPOINT=jaeger:4317
EOF

echo "✓ Service configuration template created"
echo "✓ All services configured with fixed passwords"
echo "✓ Configuration completed successfully" 