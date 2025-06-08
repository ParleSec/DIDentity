# DIDentity Vault Integration

[![Vault](https://img.shields.io/badge/HashiCorp-Vault-blue?style=for-the-badge&logo=vault)](https://www.vaultproject.io/) (https://www.vaultproject.io/) [![Docker](https://img.shields.io/badge/Deployment-Docker-blue?style=for-the-badge&logo=docker)](https://docker.com/)

This directory contains the **HashiCorp Vault integration** for the DIDentity platform, providing secret management, automatic credential generation, and comprehensive security features.

## 🎯 Overview

The DIDentity Vault integration eliminates hardcoded secrets and provides centralized, secure secret management for all platform components. This implementation demonstrates best practices for secret management in microservices architectures.

### **Key Benefits**

- **🔒 Zero Hardcoded Secrets**: Complete elimination of hardcoded credentials
- **🔄 Automatic Secret Generation**: Cryptographically secure password generation
- **📊 Centralized Management**: Single source of truth for all secrets
- **📝 Audit Trail**: Complete logging of all secret access and modifications
- **🔄 Secret Rotation**: Built-in support for credential lifecycle management
- **🛡️ Fallback Mechanisms**: Graceful degradation with environment variable fallbacks
- **⚡ Performance Optimization**: Intelligent caching with connection pooling

## 📁 Directory Structure

```
vault/
├── README.md                    # This comprehensive guide
├── VAULT_INTEGRATION.md         # Detailed technical documentation
├── scripts/                     # Vault setup and configuration scripts
│   ├── init_vault.sh           # Vault initialization with secret generation
│   └── configure_services.sh   # Service configuration with Vault secrets
├── vault_client.py             # Shared Vault client library
├── config/                     # Vault configuration files (auto-generated)
└── logs/                       # Vault audit logs (auto-generated)
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- HashiCorp Vault (included in docker-compose.yml)
- Access to DIDentity project root

### 1. Automatic Setup (Recommended)

The Vault integration is automatically configured when you start DIDentity:

```bash
# From DIDentity project root
docker-compose up -d
```

This will:
- Start Vault in development mode
- Initialize Vault with secure secrets
- Configure all services to use Vault
- Set up audit logging

### 2. Manual Setup (Advanced)

For manual configuration or troubleshooting:

```bash
# Initialize Vault manually
cd vault/scripts
./init_vault.sh

# Configure services manually
./configure_services.sh
```

### 3. Verify Setup

```bash
# Check Vault status
docker-compose exec vault vault status

# List all secrets
docker-compose exec vault vault kv list kv/

# Access Vault UI
open http://localhost:8200
# Token: root
```

## 🔐 Secret Organization

Secrets are organized in a hierarchical structure within Vault's KV v2 engine:

### **Secret Hierarchy**

```
kv/
├── database/config              # PostgreSQL Configuration
│   ├── host: postgres
│   ├── port: 5432
│   ├── database: dididentity
│   ├── username: postgres
│   └── password: VaultSecureDB2024
│
├── rabbitmq/config              # RabbitMQ Configuration
│   ├── username: admin
│   ├── password: VaultSecureRMQ2024
│   ├── host: rabbitmq
│   ├── port: 5672
│   └── management_port: 15672
│
├── auth/jwt                     # JWT Configuration
│   ├── secret_key: [auto-generated-256-bit]
│   ├── algorithm: HS256
│   ├── access_token_expire_minutes: 30
│   └── refresh_token_expire_days: 7
│
├── grafana/config               # Grafana Configuration
│   ├── admin_user: admin
│   ├── admin_password: VaultSecureGrafana2024
│   ├── secret_key: [auto-generated]
│   └── database_url: [auto-generated]
│
├── security/encryption          # Encryption Keys
│   ├── master_key: [auto-generated-512-bit]
│   ├── data_encryption_key: [auto-generated-256-bit]
│   └── signing_key: [auto-generated-256-bit]
│
├── monitoring/config            # Monitoring Configuration
│   ├── prometheus_url: http://prometheus:9090
│   ├── jaeger_url: http://jaeger:16686
│   ├── grafana_url: http://grafana:3000
│   └── alert_webhook: [configurable]
│
└── services/api_keys            # Service API Keys
    ├── auth_service: [auto-generated-uuid]
    ├── did_service: [auto-generated-uuid]
    ├── credential_service: [auto-generated-uuid]
    ├── verification_service: [auto-generated-uuid]
    └── monitoring_service: [auto-generated-uuid]
```

### **Secret Types**

| Secret Type | Generation Method | Rotation | Usage |
|-------------|------------------|----------|-------|
| **Passwords** | Cryptographic random (32 chars) | Manual/Automated | Service authentication |
| **API Keys** | UUID v4 | Manual | Inter-service communication |
| **Encryption Keys** | Cryptographic random (256/512 bit) | Manual | Data encryption/signing |
| **JWT Secrets** | Cryptographic random (256 bit) | Manual | Token signing |

## 🛠️ Vault Client Library

The `vault_client.py` provides a comprehensive Python client for interacting with Vault:

### **Features**

- **Connection Management**: Automatic connection handling with retry logic
- **Caching**: 5-minute TTL caching for performance optimization
- **Error Handling**: Comprehensive error handling with fallback mechanisms
- **Convenience Methods**: Pre-built methods for common secret retrieval
- **Thread Safety**: Safe for use in multi-threaded applications

### **Usage Examples**

```python
from vault_client import VaultClient, VaultClientError

# Initialize client
vault_client = VaultClient()

# Get database configuration
try:
    db_config = vault_client.get_database_config()
    print(f"Database URL: {vault_client.get_database_url()}")
except VaultClientError as e:
    print(f"Vault error: {e}")

# Get specific secret
secret_value = vault_client.get_secret('database/config', 'password')

# Get JWT configuration
jwt_config = vault_client.get_jwt_config()
secret_key = jwt_config['secret_key']

# Health check
health = vault_client.health_check()
print(f"Vault status: {health['status']}")
```

### **Available Methods**

| Method | Description | Returns |
|--------|-------------|---------|
| `get_database_config()` | PostgreSQL configuration | Dict with connection details |
| `get_database_url()` | PostgreSQL connection URL | String |
| `get_rabbitmq_config()` | RabbitMQ configuration | Dict with credentials |
| `get_jwt_config()` | JWT configuration | Dict with keys and settings |
| `get_grafana_config()` | Grafana configuration | Dict with admin credentials |
| `get_encryption_keys()` | Encryption keys | Dict with various keys |
| `get_service_api_key(service)` | Service API key | String |
| `health_check()` | Vault health status | Dict with status info |

## 🔧 Configuration Scripts

### **init_vault.sh**

Initializes Vault with all required secrets:

```bash
#!/bin/bash
# Vault initialization script

# Features:
# - Enables KV v2 secrets engine
# - Generates cryptographically secure passwords
# - Creates hierarchical secret structure
# - Enables audit logging
# - Verifies secret storage

./init_vault.sh
```

**Key Functions:**
- **Secret Generation**: Uses `/dev/urandom` and `base64` for secure random generation
- **Audit Logging**: Enables file-based audit logging to `vault/logs/audit.log`
- **Verification**: Confirms all secrets are properly stored
- **Error Handling**: Comprehensive error checking and reporting

### **configure_services.sh**

Configures services to use Vault secrets:

```bash
#!/bin/bash
# Service configuration script

# Features:
# - Retrieves secrets from Vault
# - Generates service configuration files
# - Updates environment variables
# - Validates configuration

./configure_services.sh
```

**Configuration Files Generated:**
- Database connection configurations
- RabbitMQ service configurations
- Grafana provisioning configurations
- Service environment files

## 🔍 Monitoring and Observability

### **Vault Health Monitoring**

The DIDentity monitoring dashboard includes comprehensive Vault monitoring:

- **Health Status**: Real-time Vault health checks
- **Secret Access**: Monitoring of secret retrieval operations
- **Performance Metrics**: Cache hit rates and response times
- **Error Tracking**: Failed authentication and access attempts

### **Audit Logging**

Vault audit logs are stored in `vault/logs/audit.log` and include:

```json
{
  "time": "2024-01-15T10:30:00Z",
  "type": "request",
  "auth": {
    "client_token": "hmac-sha256:...",
    "accessor": "hmac-sha256:..."
  },
  "request": {
    "operation": "read",
    "path": "kv/data/database/config",
    "data": null
  },
  "response": {
    "status": 200
  }
}
```

### **Metrics Available**

- Secret retrieval frequency
- Cache hit/miss ratios
- Authentication success/failure rates
- Response time distributions
- Error rates by secret path

## 🔒 Security Features

### **Development Mode Security**

Current setup uses Vault development mode with:

- **Root Token**: `root` (for development only)
- **In-Memory Storage**: Data persists only during container lifetime
- **HTTP Communication**: Unencrypted (development only)
- **Auto-Unseal**: Automatic unsealing on startup

### **Production Security Recommendations**

For production deployment:

1. **Storage Backend**: Use Consul, etcd, or cloud storage
2. **Authentication**: Implement AppRole or Kubernetes auth
3. **TLS Encryption**: Enable TLS for all Vault communication
4. **Auto-Unseal**: Use cloud KMS for automatic unsealing
5. **Network Security**: Implement proper network segmentation
6. **Backup Strategy**: Regular secret backups and disaster recovery
7. **Monitoring**: Comprehensive metrics and alerting

### **Secret Rotation Strategy**

```bash
# Example rotation workflow
# 1. Generate new secret
vault kv put kv/database/config password="NewSecurePassword2024"

# 2. Update service configuration
./configure_services.sh

# 3. Restart services with new credentials
docker-compose restart auth-service did-service credential-service verification-service

# 4. Verify connectivity
curl http://localhost:8080/api/health
```

## 🚨 Troubleshooting

### **Common Issues**

#### **Vault Container Not Starting**

```bash
# Check Vault logs
docker-compose logs vault

# Common solutions:
# 1. Port 8200 already in use
sudo lsof -i :8200
# Kill conflicting process or change port

# 2. Permission issues
sudo chown -R $(whoami) vault/logs vault/config
```

#### **Secret Retrieval Failures**

```bash
# Test Vault connectivity
docker-compose exec vault vault status

# Check authentication
docker-compose exec vault vault auth -method=token token=root

# Verify secret exists
docker-compose exec vault vault kv get kv/database/config
```

#### **Service Configuration Issues**

```bash
# Re-run configuration
cd vault/scripts
./configure_services.sh

# Check generated configurations
ls -la ../config/

# Verify environment variables
docker-compose exec auth-service env | grep VAULT
```

### **Debug Mode**

Enable debug logging in `vault_client.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

vault_client = VaultClient()
# Will output detailed debug information
```

### **Health Checks**

```bash
# Comprehensive health check
curl http://localhost:8080/api/health

# Vault-specific health
curl http://localhost:8200/v1/sys/health

# Service connectivity test
curl http://localhost:8080/api/test/workflow
```

## 📚 Advanced Usage

### **Custom Secret Management**

Add new secrets to Vault:

```bash
# 1. Add to init_vault.sh
vault kv put kv/custom/config \
  api_key="$(generate_secure_key)" \
  endpoint="https://api.example.com"

# 2. Add to vault_client.py
def get_custom_config(self):
    return self.get_secret('custom/config')

# 3. Use in services
from vault_client import VaultClient
vault_client = VaultClient()
custom_config = vault_client.get_custom_config()
```

### **Secret Versioning**

Vault KV v2 supports secret versioning:

```bash
# View secret versions
vault kv metadata kv/database/config

# Get specific version
vault kv get -version=2 kv/database/config

# Rollback to previous version
vault kv rollback -version=1 kv/database/config
```

### **Policy Management**

Create custom Vault policies:

```bash
# Create policy file
cat > database-policy.hcl << EOF
path "kv/data/database/*" {
  capabilities = ["read"]
}
EOF

# Apply policy
vault policy write database-readonly database-policy.hcl

# Create token with policy
vault token create -policy=database-readonly
```

## 🔄 Migration and Backup

### **Backup Secrets**

```bash
# Export all secrets
vault kv export kv/ > vault-backup-$(date +%Y%m%d).json

# Backup specific path
vault kv export kv/database > database-backup.json
```

### **Restore Secrets**

```bash
# Import secrets
vault kv import kv/ @vault-backup-20240115.json

# Verify restoration
vault kv list kv/
```

### **Migration Between Environments**

```bash
# Export from development
vault kv export kv/ > dev-secrets.json

# Import to production (after proper security setup)
vault kv import kv/ @dev-secrets.json
```

## 📖 Additional Resources

- **[HashiCorp Vault Documentation](https://www.vaultproject.io/docs)**: Official Vault documentation
- **[Vault API Reference](https://www.vaultproject.io/api-docs)**: Complete API documentation
- **[Security Best Practices](https://learn.hashicorp.com/vault/security)**: Vault security guidelines


## 📄 License

This Vault integration is part of the DIDentity project and is licensed under the MIT License.

---

<div align="center">
<i>ParleSec</i>
</div> 