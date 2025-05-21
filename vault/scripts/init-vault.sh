#!/bin/sh
set -e

# Wait for Vault to be ready
echo "Waiting for Vault to start..."
until vault status >/dev/null 2>&1; do
  echo "Vault not ready yet, retrying in 2 seconds..."
  sleep 2
done
echo "Vault is ready"

# Log in to Vault with root token
echo "Logging in to Vault"
vault login root

# Check if KV secrets engine is already enabled
if ! vault secrets list | grep -q "secret/"; then
  echo "Enabling KV secrets engine"
  vault secrets enable -path=secret kv-v2
else
  echo "KV secrets engine already enabled"
fi

# Create policy for services
echo "Creating services policy"
vault policy write services-policy - <<EOF
path "secret/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# Create a token for services with appropriate policy
echo "Creating service token"
TOKEN=$(vault token create -policy=services-policy -format=json | jq -r ".auth.client_token")
echo "Service token: $TOKEN"

# Store the token in a known location
echo "Storing token in /vault/data/service-token"
echo $TOKEN > /vault/data/service-token
chmod 644 /vault/data/service-token

# Store database credentials
echo "Storing database credentials"
vault kv put secret/database/config username=postgres password=postgres

# Store JWT secret for auth service
echo "Storing JWT secret"
vault kv put secret/auth/jwt secret="$(openssl rand -base64 32)"

# Store RabbitMQ credentials
echo "Storing RabbitMQ credentials"
vault kv put secret/rabbitmq/config username=guest password=guest

echo "Vault initialization complete!" 