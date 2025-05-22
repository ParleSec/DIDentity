# DIDentity

A decentralized identity platform based on microservices architecture, implementing DIDs, Verifiable Credentials, and secure authentication.

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

## Getting Started

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
   docker-compose up -d
   ```

3. The services will be available at:
   - Auth Service: http://localhost:8004
   - DID Service: http://localhost:8001
   - Credential Service: http://localhost:8002
   - Verification Service: http://localhost:8003
   - RabbitMQ Management: http://localhost:15672 (guest/guest)
   - Vault UI: http://localhost:8200 (token: root)
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090
   - Jaeger UI: http://localhost:16686

## Features

- **Secure Authentication**: JWT-based authentication with refresh tokens
- **DID Management**: Create and resolve DIDs using various methods (ethr, web, key)
- **Verifiable Credentials**: Issue, manage, and verify credentials
- **Event-Driven Architecture**: Microservices communicate via events
- **Secret Management**: Secure storage of secrets with HashiCorp Vault
- **Distributed Tracing**: Track requests across services with OpenTelemetry
- **Monitoring**: Complete observability with Prometheus and Grafana

## Example Usage

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

## Development

### Project Structure

```
DIDentity/
├── auth-service/             # Authentication service
├── did-service/              # DID management service
├── credential-service/       # Credential service
├── verification-service/     # Verification service
├── monitoring/               # Monitoring configuration
├── vault/                    # Vault configuration and scripts
├── tests/                    # Test suites
├── docker-compose.yml        # Docker Compose configuration
└── README.md                 # This file
```
