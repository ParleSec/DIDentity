# DIDentity

[![Microservices](https://img.shields.io/badge/Architecture-Microservices-blue?style=for-the-badge&logo=docker)](https://docker.com/) [![Python](https://img.shields.io/badge/Backend-Python-blue?style=for-the-badge&logo=python)](https://www.python.org/)[![Infrastructure](https://img.shields.io/badge/Infrastructure-Docker%20%7C%20Vault%20%7C%20RabbitMQ-purple?style=for-the-badge&logo=docker)](https://docker.com/) [![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**DIDentity** is a comprehensive decentralized identity platform based on microservices architecture, implementing DIDs (Decentralized Identifiers), Verifiable Credentials, and secure authentication. Built with security and scalability in mind, DIDentity provides a complete solution for managing digital identity in a decentralized environment.

## Purpose & Motivation

Modern digital identity requires secure, user-controlled, and interoperable solutions. DIDentity aims to:

- Provide a complete implementation of W3C DID standards
- Enable secure issuance and verification of Verifiable Credentials
- Implement robust authentication mechanisms
- Offer a scalable, microservices-based architecture
- Create an extensible platform for decentralized identity use cases

## Quick Installation

### Prerequisites

- Docker and Docker Compose
- Git

### Setup and Run

1. Clone the repository:
   ```bash
   git clone https://github.com/ParleSec/DIDentity.git
   cd DIDentity
   ```

2. Start the services using Docker Compose:
   ```bash
   sudo docker-compose up -d
   ```

3. The services will be available at:
   - **Monitoring Dashboard**: http://localhost:8080 (Unified monitoring interface)
   - **Auth Service**: http://localhost:8004
   - **DID Service**: http://localhost:8001
   - **Credential Service**: http://localhost:8002
   - **Verification Service**: http://localhost:8003
   - **RabbitMQ Management**: http://localhost:15672 (credentials managed by Vault)
   - **Vault UI**: http://localhost:8200 (token: root)
   - **Grafana**: http://localhost:3000 (credentials managed by Vault)
   - **Prometheus**: http://localhost:9090
   - **Jaeger UI**: http://localhost:16686

## Architecture

DIDentity consists of several microservices:
- **Auth Service**: User authentication and authorization (port 8004)
- **DID Service**: Decentralized Identifier (DID) management (port 8001)
- **Credential Service**: Verifiable Credentials issuance and management (port 8002)
- **Verification Service**: Verification of Credentials (port 8003)

The platform uses:
- **PostgreSQL**: For persistent data storage
- **HashiCorp Vault**: For comprehensive secrets management
- **RabbitMQ**: For event-driven communication between services
- **Jaeger**: For distributed tracing
- **Prometheus/Grafana**: For monitoring and alerting

## Key Features

### 🔐 Core Identity Components
- **Decentralized Identifiers (DIDs)** implementation with multiple methods (ethr, web, key)
- **Verifiable Credentials** issuance, management, and verification
- **Secure Authentication** with JWT-based tokens and refresh mechanism
- **Event-Driven Architecture** for reliable communication between services

### 🖥️ Service Architecture
- **Auth Service**: User authentication and authorization (port 8004)
- **DID Service**: Decentralized Identifier (DID) management (port 8001)
- **Credential Service**: Verifiable Credentials issuance and management (port 8002)
- **Verification Service**: Verification of Credentials (port 8003)

### 🛡️ Security & Infrastructure
- **HashiCorp Vault**: Comprehensive secret management with automatic secret generation
- **PostgreSQL**: Reliable persistent data storage with Vault-managed credentials
- **RabbitMQ**: Event-driven communication with secure Vault-managed authentication
- **OpenTelemetry**: Distributed tracing with Jaeger
- **Prometheus/Grafana**: Comprehensive monitoring with secure Vault-managed access

### 🔒 Vault Integration Features

DIDentity now includes comprehensive HashiCorp Vault integration for secure secret management:

- **Centralized Secret Storage**: All sensitive data stored securely in Vault
- **Dynamic Secret Generation**: Automatic generation of secure random passwords
- **Secret Rotation Support**: Built-in capabilities for credential rotation
- **Audit Logging**: Complete audit trail of all secret access
- **Fallback Mechanisms**: Graceful degradation with environment variable fallbacks
- **Caching**: Performance optimization with 5-minute TTL secret caching

#### Vault-Managed Secrets

All the following secrets are automatically generated and managed by Vault:

- Database passwords and connection strings
- RabbitMQ credentials and management access
- Grafana admin credentials and secret keys
- JWT signing keys and configuration
- Service API keys for inter-service communication
- Encryption keys for data protection

#### Security Benefits

1. **No Hardcoded Secrets**: All credentials dynamically retrieved from Vault
2. **Centralized Management**: Single source of truth for all secrets
3. **Automatic Generation**: Secure random password generation
4. **Access Control**: Token-based authentication to Vault
5. **Audit Trail**: Complete logging of secret access and modifications

## Service Architecture

### Microservices Implementation

DIDentity uses a microservices architecture providing:
- **Scalability** through independent service scaling
- **Resilience** through service isolation
- **Flexibility** through technology independence
- **Maintainability** through focused codebases
- **Event-Driven** communication via RabbitMQ
- **REST APIs** for service interfaces
- **Asynchronous processing** of long-running tasks

### Monitoring and Observability

- **Distributed Tracing** with OpenTelemetry and Jaeger
- **Metrics Collection** with Prometheus
- **Visualization** with Grafana dashboards
- **Log Aggregation** across all services
- **Health Monitoring** with Vault status integration

### Security Implementation

- **Secret Management** with HashiCorp Vault
- **JWT Authentication** for secure API access
- **Cryptographic Operations** for credential signatures
- **Secure Communication** between services
- **Audit Logging** for all secret access

## Vault Secret Management

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

### Accessing Vault

- **Vault UI**: http://localhost:8200 (token: root)
- **CLI Access**: Use `vault` commands with `VAULT_ADDR=http://localhost:8200` and `VAULT_TOKEN=root`

### Vault Commands

```bash
# Check Vault status
vault status

# List all secrets
vault kv list kv/

# Get database configuration
vault kv get kv/database/config

# Get specific secret value
vault kv get -field=password kv/database/config
```

For detailed information about the Vault integration, see [vault/VAULT_INTEGRATION.md](vault/VAULT_INTEGRATION.md).

## API Examples

### Create a User

```bash
curl -X POST http://localhost:8004/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'
```

### Create a DID

```bash
curl -X POST http://localhost:8001/dids \
  -H "Content-Type: application/json" \
  -d '{"method":"ethr","identifier":"0x1234567890abcdef1234567890abcdef12345678"}'
```

### Resolve a DID

```bash
curl http://localhost:8001/dids/did:ethr:0x1234567890abcdef1234567890abcdef12345678
```

### Issue a Credential

```bash
curl -X POST http://localhost:8002/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "issuerDid": "did:ethr:0x1234567890abcdef1234567890abcdef12345678",
    "subjectDid": "did:ethr:0x9876543210abcdef1234567890abcdef12345678",
    "type": ["VerifiableCredential", "EducationCredential"],
    "claims": {
      "degree": "Bachelor of Science",
      "institution": "Example University"
    }
  }'
```

### Verify a Credential

```bash
curl -X POST http://localhost:8003/verify \
  -H "Content-Type: application/json" \
  -d '{
    "credential": {
      // Credential JSON
    }
  }'
```

## Getting Started

### Service Access Points

After starting the services, they will be available at:

- **Monitoring Dashboard**: http://localhost:8080 (Unified system monitoring)
- **Auth Service**: http://localhost:8004
- **DID Service**: http://localhost:8001
- **Credential Service**: http://localhost:8002
- **Verification Service**: http://localhost:8003
- **RabbitMQ Management**: http://localhost:15672 (credentials in Vault)
- **Vault UI**: http://localhost:8200 (token: root)
- **Grafana**: http://localhost:3000 (credentials in Vault)
- **Prometheus**: http://localhost:9090
- **Jaeger UI**: http://localhost:16686

### Basic Usage Flow

1. Access the Monitoring Dashboard at http://localhost:8080 to monitor system health
2. Check Vault status and secrets at http://localhost:8200
3. Create a user account
4. Generate a new DID
5. Issue a Verifiable Credential
6. Verify the credential

### Accessing Credentials

All service credentials are managed by Vault. To access them:

1. **Via Vault UI**: Navigate to http://localhost:8200 and browse the `kv/` secrets
2. **Via CLI**: Use vault commands as shown above
3. **Via Monitoring Dashboard**: View Vault status and health information

## Project Structure

```
DIDentity/
├── auth-service/             # Authentication service
│   └── src/                  # Auth service source code
├── did-service/              # DID management service
│   └── src/                  # DID service source code
├── credential-service/       # Credential service
│   └── src/                  # Credential service source code
├── verification-service/     # Verification service
│   └── src/                  # Verification service source code
├── vault/                    # Vault configuration and scripts
│   ├── scripts/              # Vault initialization and configuration scripts
│   ├── vault_client.py       # Shared Vault client library
│   └── VAULT_INTEGRATION.md  # Detailed Vault documentation
├── monitoring/               # Monitoring configuration
│   └── grafana/              # Grafana dashboards and config
├── monitoring-dashboard/     # Unified monitoring dashboard
└── docker-compose.yml        # Complete service orchestration
```

## Security Features

### Vault Integration Benefits

- **No Hardcoded Secrets**: All sensitive data managed by Vault
- **Automatic Secret Generation**: Secure random passwords for all services
- **Centralized Management**: Single point of control for all secrets
- **Audit Logging**: Complete trail of secret access and modifications
- **Secret Rotation**: Built-in support for credential rotation
- **Fallback Mechanisms**: Graceful degradation if Vault unavailable

### Production Considerations

For production deployment:

1. **Use Vault in Production Mode**: Configure with proper storage backend
2. **Implement Auto-Unseal**: Use cloud KMS for automatic unsealing
3. **Set Up Authentication**: Use AppRole or Kubernetes authentication
4. **Configure TLS**: Enable TLS for all Vault communication
5. **Backup Strategy**: Implement regular secret backups
6. **Monitoring**: Set up Vault metrics and alerting

See [vault/VAULT_INTEGRATION.md](vault/VAULT_INTEGRATION.md) for detailed production guidance.

## Development

### Running in Development

The current setup is optimized for development with:
- Vault in development mode
- Automatic secret initialization
- Simplified authentication
- Local storage

### Adding New Secrets

To add new secrets to Vault:

1. Update `vault/scripts/init_vault.sh` to include the new secret
2. Add convenience methods to `vault/vault_client.py`
3. Update services to use the new secret
4. Document the changes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the documentation in `vault/VAULT_INTEGRATION.md`
- Review the monitoring dashboard for system health

---

<div align="center">
<i>DIDentity - ParleSec</i>
</div>
