# Vault Integration for DIDentity

This document describes the comprehensive HashiCorp Vault integration implemented in the DIDentity project for secure secret management.

## Overview

The DIDentity project now uses HashiCorp Vault to securely store and manage all sensitive information including:

- Database credentials
- RabbitMQ credentials  
- Grafana admin credentials
- JWT secret keys
- Encryption keys
- Service API keys
- Monitoring configuration

## Architecture

### Components

1. **Vault Server**: HashiCorp Vault running in development mode
2. **Vault Initialization**: Automated setup of secrets and policies
3. **Vault Client Library**: Shared Python library for secret retrieval
4. **Service Configuration**: Dynamic configuration of services with Vault secrets
5. **Fallback Mechanisms**: Environment variable fallbacks for resilience

### Secret Organization

Secrets are organized in Vault using the following structure:

```
kv/
├── database/config          # Database connection details
├── rabbitmq/config          # RabbitMQ credentials and settings
├── auth/jwt                 # JWT configuration and keys
├── grafana/config           # Grafana admin credentials
├── security/encryption      # Master encryption keys
├── monitoring/config        # Monitoring endpoints and settings
└── services/api_keys        # Service-specific API keys
```

## Security Benefits

### 1. Centralized Secret Management
- All secrets stored in a single, secure location
- Consistent access patterns across services
- Centralized audit logging

### 2. Dynamic Secret Generation
- Passwords are randomly generated during initialization
- No hardcoded credentials in configuration files
- Automatic rotation capabilities

### 3. Access Control
- Token-based authentication to Vault
- Granular permissions (future enhancement)
- Audit trail of all secret access

### 4. Encryption at Rest and in Transit
- All secrets encrypted in Vault storage
- TLS communication between services and Vault
- Memory-safe secret handling

### 5. Secret Rotation
- Built-in support for secret rotation
- Cache invalidation on secret updates
- Zero-downtime credential updates

## Implementation Details

### Vault Client Library

The shared Vault client library provides:

```python
from vault_client import VaultClient, VaultClientError

# Initialize client
vault_client = VaultClient()

# Retrieve secrets
db_url = vault_client.get_database_url()
jwt_key = vault_client.get_jwt_secret_key()
rabbitmq_config = vault_client.get_rabbitmq_config()

# Health checking
health = vault_client.health_check()
```

### Features

- **Automatic Caching**: 5-minute TTL cache for performance
- **Retry Logic**: Exponential backoff for failed requests
- **Error Handling**: Graceful degradation with fallbacks
- **Thread Safety**: Safe for concurrent access
- **Health Monitoring**: Built-in health check capabilities

## Configuration Process

### 1. Vault Initialization

```bash
# Vault starts in development mode
vault server -dev -dev-root-token-id=root

# Initialization script runs
./vault/scripts/init_vault.sh
```

### 2. Secret Generation

The initialization script:
- Generates secure random passwords
- Creates all required secret paths
- Enables audit logging
- Verifies secret storage

### 3. Service Configuration

```bash
# Configuration script retrieves secrets
./vault/scripts/configure_services.sh

# Generates environment files and configs
# Services start with Vault-managed secrets
```

### 4. Runtime Operation

Services retrieve secrets dynamically:
- First attempt: Vault API
- Fallback: Environment variables
- Cache: 5-minute TTL for performance

## Usage Examples

### Retrieving Database Configuration

```python
# Using the Vault client
from vault_client import vault_client

# Get full database config
db_config = vault_client.get_database_config()

# Get specific values
db_url = vault_client.get_database_url()
db_password = vault_client.get_secret('database/config', 'password')
```

### Service Authentication

```python
# JWT secret retrieval
jwt_secret = vault_client.get_jwt_secret_key()

# Service API key
api_key = vault_client.get_service_api_key('auth')
```

### Health Monitoring

```python
# Check Vault health
health = vault_client.health_check()
```

## Security Best Practices

### Current Implementation

1. ✅ **Centralized Secret Storage**: All secrets in Vault
2. ✅ **Dynamic Secret Generation**: Random password generation
3. ✅ **Audit Logging**: All access logged
4. ✅ **Encryption**: Secrets encrypted at rest
5. ✅ **Access Control**: Token-based authentication

### Future Enhancements

1. **Role-Based Access**: Service-specific permissions
2. **Secret Rotation**: Automated credential rotation
3. **Policy Enforcement**: Fine-grained access policies
4. **Multi-Factor Auth**: Additional authentication layers
5. **Secret Scanning**: Detect leaked credentials

## Troubleshooting

### Common Issues

1. **Vault Unavailable**
   - Services fall back to environment variables
   - Check Vault container status
   - Verify network connectivity

2. **Authentication Failures**
   - Verify VAULT_TOKEN environment variable
   - Check token expiration
   - Review Vault logs

3. **Secret Not Found**
   - Verify secret path exists in Vault
   - Check initialization script completion
   - Review audit logs

### Debug Commands

```bash
# Check Vault status
vault status

# List secrets
vault kv list kv/

# Get specific secret
vault kv get kv/database/config

# Test service health
curl http://localhost:8004/health
```

## Conclusion

The Vault integration provides a robust, secure foundation for secret management in the DIDentity project. It eliminates hardcoded credentials, provides centralized secret management, and enables secure, scalable operations. 