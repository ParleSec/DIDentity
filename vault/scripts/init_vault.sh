#!/bin/sh

# Vault initialization script with fixed passwords


set -e

echo "=== Simple Vault Initialization ==="

export VAULT_ADDR=http://vault:8200
export VAULT_TOKEN=root

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if vault status > /dev/null 2>&1; then
    echo "✓ Vault is ready"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT+1))
  echo "Attempt $RETRY_COUNT of $MAX_RETRIES: Vault not ready, waiting 2 seconds..."
  sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "ERROR: Vault not ready after $MAX_RETRIES attempts"
  exit 1
fi

# Use fixed passwords for consistency across restarts
FIXED_DB_PASSWORD="VaultSecureDB2024"
FIXED_RABBITMQ_PASSWORD="VaultSecureRMQ2024"
FIXED_GRAFANA_PASSWORD="VaultSecureGrafana2024"

echo "=== Setting up KV secrets engine ==="
if vault secrets list | grep -q "^kv/"; then
  echo "✓ KV secrets engine already enabled"
else
  echo "Enabling KV v2 secrets engine..."
  vault secrets enable -path=kv -version=2 kv
  echo "✓ KV secrets engine enabled"
fi

echo "=== Creating secrets with fixed passwords ==="

# Database configuration - fixed password
echo "Setting database secrets..."
vault kv put kv/database/config \
  host=db \
  port=5432 \
  database=decentralized_id \
  username=postgres \
  password="$FIXED_DB_PASSWORD"
echo "✓ Database secrets set"

# RabbitMQ configuration - fixed password
echo "Setting RabbitMQ secrets..."
vault kv put kv/rabbitmq/config \
  host=rabbitmq \
  port=5672 \
  management_port=15672 \
  username=admin \
  password="$FIXED_RABBITMQ_PASSWORD" \
  vhost=/
echo "✓ RabbitMQ secrets set"

# JWT configuration
echo "Setting JWT secrets..."
vault kv put kv/auth/jwt \
  secret_key="VaultJWTSecret2024SuperSecure" \
  algorithm=HS256 \
  expiration_hours=24
echo "✓ JWT secrets set"

# Grafana configuration
echo "Setting Grafana secrets..."
vault kv put kv/grafana/config \
  admin_user=admin \
  admin_password="$FIXED_GRAFANA_PASSWORD" \
  secret_key="VaultGrafanaSecret2024"
echo "✓ Grafana secrets set"

# Security/Encryption keys
echo "Setting security secrets..."
vault kv put kv/security/encryption \
  master_key="VaultMasterKey2024SuperSecure" \
  data_key="VaultDataKey2024SuperSecure" \
  signing_key="VaultSigningKey2024SuperSecure"
echo "✓ Security secrets set"

# Monitoring configuration
echo "Setting monitoring secrets..."
vault kv put kv/monitoring/config \
  prometheus_url=http://prometheus:9090 \
  grafana_url=http://grafana:3000 \
  jaeger_url=http://jaeger:16686
echo "✓ Monitoring secrets set"

# Service API keys
echo "Setting service API keys..."
vault kv put kv/services/api_keys \
  auth_service="VaultAuthAPI2024" \
  did_service="VaultDIDAPI2024" \
  credential_service="VaultCredAPI2024" \
  verification_service="VaultVerifyAPI2024"
echo "✓ Service API keys set"

echo "=== Setting up audit logging ==="
vault audit enable file file_path=/vault/logs/audit.log || echo "✓ Audit logging already enabled"

echo "=== Vault Initialization Complete ==="
echo "✓ All secrets stored with fixed passwords"
echo "✓ No restart synchronization issues"
echo ""
echo "Database password: $FIXED_DB_PASSWORD"
echo "RabbitMQ password: $FIXED_RABBITMQ_PASSWORD"
echo "Grafana password: $FIXED_GRAFANA_PASSWORD"