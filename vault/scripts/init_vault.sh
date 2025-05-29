#!/bin/sh

# Wait for Vault to start and be ready
echo "Waiting for Vault to start..."
sleep 10

export VAULT_ADDR=http://vault:8200
export VAULT_TOKEN=root

echo "Attempting to connect to Vault..."

# Robust check for Vault availability with retries
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if vault status > /dev/null 2>&1; then
    echo "Successfully connected to Vault"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT+1))
  echo "Attempt $RETRY_COUNT of $MAX_RETRIES: Vault not ready, waiting 2 seconds..."
  sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Failed to connect to Vault after $MAX_RETRIES attempts. Exiting."
  exit 1
fi

echo "Vault is up and running. Initializing secrets..."

# Enable the KV secrets engine if not already enabled
if vault secrets list | grep -q "^kv/"; then
  echo "KV secrets engine already enabled"
else
  echo "Enabling KV secrets engine..."
  vault secrets enable -version=2 kv
  if [ $? -eq 0 ]; then
    echo "KV secrets engine enabled successfully"
  else
    echo "Failed to enable KV secrets engine"
    exit 1
  fi
fi

# Create secrets for database with error handling
echo "Writing database secrets..."
if vault kv put kv/database/config \
  url="postgresql://postgres:password@db:5432/decentralized_id" \
  username="postgres" \
  password="password"; then
  echo "Database secrets created successfully"
else
  echo "Failed to write database secrets"
  exit 1
fi

# Create secrets for JWT with error handling
echo "Writing JWT secrets..."
if vault kv put kv/auth/jwt \
  secret_key="secure-random-generated-secret-key" \
  algorithm="HS256" \
  token_expire_minutes="30" \
  refresh_token_expire_days="7"; then
  echo "JWT secrets created successfully"
else
  echo "Failed to write JWT secrets"
  exit 1
fi

# Verify secrets were stored correctly
echo "Verifying secrets..."
if vault kv get kv/database/config > /dev/null 2>&1 && vault kv get kv/auth/jwt > /dev/null 2>&1; then
  echo "Verification successful: All secrets are stored correctly"
else
  echo "Verification failed: Some secrets might not be stored correctly"
  exit 1
fi

echo "Vault initialization completed successfully!"
echo "In a production environment, secure the root token and unseal keys appropriately."