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
   - **RabbitMQ Management**: http://localhost:15672 (guest/guest)
   - **Vault UI**: http://localhost:8200 (token: root)
   - **Grafana**: http://localhost:3000 (admin/admin)
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
- **HashiCorp Vault**: For secrets management
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
- **HashiCorp Vault**: Secure storage and management of secrets
- **PostgreSQL**: Reliable persistent data storage
- **RabbitMQ**: Event-driven communication between services
- **OpenTelemetry**: Distributed tracing with Jaeger
- **Prometheus/Grafana**: Comprehensive monitoring and alerting

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

### Security Implementation

- **Secret Management** with HashiCorp Vault
- **JWT Authentication** for secure API access
- **Cryptographic Operations** for credential signatures
- **Secure Communication** between services

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

- Auth Service: http://localhost:8004
- DID Service: http://localhost:8001
- Credential Service: http://localhost:8002
- Verification Service: http://localhost:8003
- RabbitMQ Management: http://localhost:15672 (guest/guest)
- Vault UI: http://localhost:8200 (token: root)
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Jaeger UI: http://localhost:16686

### Basic Usage Flow

1. Access the Monitoring Dashboard at http://localhost:8000 to monitor system health
2. Create a user account
3. Generate a new DID
4. Issue a Verifiable Credential
5. Verify the credential

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
├── monitoring/               # Monitoring configuration
│   └── grafana/              # Grafana dashboards and config
├── vault/                    # Vault configuration and scripts
├── tests/                    # Test suites
│   ├── e2e/                  # End-to-end tests
│   ├── integration/          # Integration tests
│   └── unit/                 # Unit tests
├── utils/                    # Utility scripts
├── templates/                # Template files
├── docker-compose.yml        # Docker Compose configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```

## Technical Details

### DID Implementation

- Support for multiple DID methods (ethr, web, key)
- Complete DID resolution
- DID document management
- Key management and rotation

### Verifiable Credentials

- W3C Verifiable Credentials data model
- JSON-LD and JWT credential formats
- Credential issuance and revocation
- Selective disclosure capabilities
- Verification protocols

### Authentication

- JWT-based authentication
- Refresh token mechanism
- Role-based access control
- OAuth 2.0 compatibility

### Infrastructure

- Containerized deployment with Docker
- Service discovery
- Secret management with Vault
- Message queue with RabbitMQ

## Testing

```bash
# Run all tests
python -m pytest

# Run specific test suite
pytest tests/unit/
```

## Troubleshooting

**💡 Pro Tip**: Use the **Monitoring Dashboard** at http://localhost:8000 for comprehensive system monitoring and troubleshooting. The dashboard provides real-time health checks, connection testing, and detailed error diagnostics for all services.

Common issues:

1. **Service Connection Issues**: 
   - Check the Monitoring Dashboard for real-time service status
   - Ensure all containers are running with `docker-compose ps`
   - Use the dashboard's "Test Connection" buttons for detailed diagnostics

2. **Database Errors**: Check PostgreSQL logs with `docker-compose logs postgres`

3. **Authentication Failures**: Verify Vault is properly initialized and unsealed

4. **Missing Events**: Check RabbitMQ management console for queue status

5. **Monitoring Tool Issues**: 
   - Use the Monitoring Dashboard's embedded interfaces
   - Check individual tool health via the dashboard's connection tests
   - Review troubleshooting suggestions provided by the dashboard

## Disclaimer

### Security Considerations
- DIDentity implements decentralized identity standards and security practices, but no system can be guaranteed as completely secure.
- The security of your identity data depends on proper key management and access controls.
- While we strive for security best practices, software vulnerabilities may exist in DIDentity or its dependencies.

### Legal Usage
- Users are responsible for complying with all applicable laws related to identity, data protection, and privacy in their jurisdiction.
- DIDentity should not be used to create or manage fraudulent identities.
- Software is provided as-is with no warranty. Software is for educational purposes only.

### No Warranty
- DIDentity is provided "as is" without warranty of any kind, express or implied.
- The authors and contributors are not liable for any damages or liability arising from the use of this software.
- Users are responsible for implementing their own data backup strategies.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
<i>DIDentity - ParleSec</i>
</div>
