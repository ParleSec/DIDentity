# DIDentity

[![Microservices](https://img.shields.io/badge/Architecture-Microservices-blue?style=for-the-badge&logo=docker)](https://docker.com/) [![Python](https://img.shields.io/badge/Backend-Python-blue?style=for-the-badge&logo=python)](https://www.python.org/) [![Infrastructure](https://img.shields.io/badge/Infrastructure-Docker%20%7C%20Vault%20%7C%20RabbitMQ-purple?style=for-the-badge&logo=docker)](https://docker.com/) [![Security](https://img.shields.io/badge/Security-Vault%20Secured-green?style=for-the-badge&logo=vault)](https://www.vaultproject.io/) [![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**DIDentity** is a comprehensive decentralized identity platform based on microservices architecture, implementing DIDs (Decentralized Identifiers), Verifiable Credentials, and secure authentication. Built with enterprise-grade security and scalability in mind, DIDentity provides a complete solution for managing digital identity in a decentralized environment with **HashiCorp Vault integration** and **advanced monitoring capabilities**.

## 🚀 What's New

### Enhanced Monitoring Dashboard
- **Sequential Workflow Testing**: Real-time, step-by-step DIDentity workflow execution with visual progress tracking
- **Comprehensive Service Monitoring**: Detailed health checks and performance metrics for all microservices
- **Secure Authentication System**: Session-based authentication for monitoring tools with zero credential exposure
- **Interactive Testing Interface**: One-click end-to-end workflow validation with detailed results

### Enterprise Security with Vault
- **Zero Hardcoded Secrets**: Complete elimination of hardcoded credentials using HashiCorp Vault
- **Automatic Secret Management**: Dynamic generation and rotation of all service credentials
- **Audit Trail**: Complete logging of all secret access and modifications
- **Production-Ready Security**: Enterprise-grade secret management with fallback mechanisms

## Purpose & Motivation

Modern digital identity requires secure, user-controlled, and interoperable solutions. DIDentity aims to:

- Provide a complete implementation of W3C DID standards
- Enable secure issuance and verification of Verifiable Credentials
- Implement robust authentication mechanisms with enterprise-grade security
- Offer a scalable, microservices-based architecture with comprehensive monitoring
- Create an extensible platform for decentralized identity use cases
- Demonstrate best practices for secret management and system observability

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
   docker-compose up -d
   ```

3. **Access the Enhanced Monitoring Dashboard**: http://localhost:8080
   - Real-time service health monitoring
   - Interactive DIDentity workflow testing
   - Secure access to all monitoring tools
   - Comprehensive system status overview

4. The services will be available at:
   - **🖥️ Monitoring Dashboard**: http://localhost:8080 (Enhanced unified interface)
   - **🔐 Auth Service**: http://localhost:8004 (User authentication & JWT)
   - **🆔 DID Service**: http://localhost:8001 (Decentralized identifiers)
   - **📜 Credential Service**: http://localhost:8002 (Verifiable credentials)
   - **✅ Verification Service**: http://localhost:8003 (Credential verification)
   - **🐰 RabbitMQ Management**: http://localhost:15672 (Vault-secured: admin/VaultSecureRMQ2024)
   - **🔒 Vault UI**: http://localhost:8200 (token: root)
   - **📊 Grafana**: http://localhost:3000 (Vault-secured: admin/VaultSecureGrafana2024)
   - **📈 Prometheus**: http://localhost:9090 (Metrics collection)
   - **🔍 Jaeger UI**: http://localhost:16686 (Distributed tracing)

## 🎯 Key Features

### 🖥️ Enhanced Monitoring Dashboard

The centerpiece of DIDentity is the **Enhanced Monitoring Dashboard** providing:

#### **Sequential Workflow Testing**
- **Real-time Progress Tracking**: Visual step-by-step execution of the complete DIDentity workflow
- **Timing Information**: Individual step timing and total execution time
- **Interactive Controls**: Start, cancel, and retry workflow tests with one click
- **Detailed Results**: Comprehensive success/failure reporting with troubleshooting guidance
- **Professional UI**: Modern, responsive interface with smooth animations and status indicators

#### **Comprehensive Service Monitoring**
- **Service Health Status**: Real-time health checks for all microservices
- **Service-Specific Information**: Detailed functionality descriptions for each DIDentity service
- **API Endpoint Access**: Direct links to service documentation and interfaces
- **Performance Metrics**: Integration with Prometheus and Grafana for detailed analytics

#### **Secure Authentication System**
- **Session-Based Security**: HTTP-only cookies with SameSite protection
- **Zero Credential Exposure**: Credentials never sent to or stored in browser
- **Auto-Refresh Support**: Persistent sessions through dashboard auto-refresh
- **Secure Proxy**: Server-side request forwarding with pre-authenticated clients

### 🔐 Core Identity Components
- **Decentralized Identifiers (DIDs)** implementation with multiple methods (key, web, ethr, sov, ion)
- **Verifiable Credentials** issuance, management, and verification with W3C standards compliance
- **Secure Authentication** with JWT-based tokens and refresh mechanism
- **Event-Driven Architecture** for reliable communication between services

### 🛡️ Enterprise Security & Infrastructure

#### **HashiCorp Vault Integration**
DIDentity includes comprehensive Vault integration for enterprise-grade security:

- **Centralized Secret Storage**: All sensitive data stored securely in Vault KV v2 engine
- **Dynamic Secret Generation**: Automatic generation of secure random passwords using cryptographic methods
- **Secret Rotation Support**: Built-in capabilities for credential rotation and lifecycle management
- **Audit Logging**: Complete audit trail of all secret access with detailed logging
- **Fallback Mechanisms**: Graceful degradation with environment variable fallbacks
- **Performance Optimization**: Intelligent caching with 5-minute TTL and connection pooling

#### **Vault-Managed Secrets**

All the following secrets are automatically generated and managed by Vault:

```
kv/
├── database/config          # PostgreSQL: VaultSecureDB2024
├── rabbitmq/config          # RabbitMQ: admin/VaultSecureRMQ2024  
├── auth/jwt                 # JWT signing keys and configuration
├── grafana/config           # Grafana: admin/VaultSecureGrafana2024
├── security/encryption      # Master encryption keys for data protection
├── monitoring/config        # Monitoring endpoints and settings
└── services/api_keys        # Service-specific API keys for inter-service communication
```

#### **Security Benefits**

1. **No Hardcoded Secrets**: All credentials dynamically retrieved from Vault
2. **Centralized Management**: Single source of truth for all secrets
3. **Automatic Generation**: Secure random password generation with cryptographic strength
4. **Access Control**: Token-based authentication to Vault with proper scoping
5. **Audit Trail**: Complete logging of secret access and modifications
6. **Restart Resilience**: Fixed passwords ensure consistent operation across container restarts

### 🏗️ Service Architecture

#### **Microservices Implementation**

DIDentity uses a microservices architecture providing:
- **Scalability** through independent service scaling
- **Resilience** through service isolation and health monitoring
- **Flexibility** through technology independence
- **Maintainability** through focused codebases and clear service boundaries
- **Event-Driven** communication via RabbitMQ with secure Vault-managed credentials
- **REST APIs** for service interfaces with comprehensive OpenAPI documentation
- **Asynchronous processing** of long-running tasks

#### **Service Details**

- **Auth Service (Port 8004)**: User registration, JWT authentication, token refresh
- **DID Service (Port 8001)**: DID creation, DID resolution, multiple method support
- **Credential Service (Port 8002)**: Credential issuance, credential management, VC standards
- **Verification Service (Port 8003)**: Credential verification, status checking, trust validation

### 📊 Monitoring and Observability

- **Enhanced Dashboard**: Unified monitoring interface with real-time workflow testing
- **Distributed Tracing** with OpenTelemetry and Jaeger for request flow analysis
- **Metrics Collection** with Prometheus for comprehensive system metrics
- **Visualization** with Grafana dashboards showing DIDentity service metrics
- **Log Aggregation** across all services with centralized logging
- **Health Monitoring** with Vault status integration and service dependency tracking

## 🧪 Interactive Workflow Testing

The Enhanced Monitoring Dashboard includes a sophisticated workflow testing system:

### **Test Complete DIDentity Workflow**

Click the "Test Complete DIDentity Workflow" button to execute:

1. **User Registration** - Creates test user with JWT authentication
2. **DID Creation** - Generates decentralized identifier using key method
3. **Credential Issuance** - Issues verifiable credential for test user  
4. **Credential Verification** - Validates credential authenticity

### **Features**

- **Real-time Progress**: Visual step-by-step execution with timing
- **Interactive Controls**: Start, cancel, and retry with one click
- **Detailed Results**: Comprehensive success/failure reporting
- **Error Handling**: Detailed troubleshooting guidance for failures
- **Professional UI**: Modern interface with animations and status indicators

### **Sample Test Results**

```json
{
  "status": "success",
  "results": {
    "user": "testuser_1749213675",
    "did": "did:DIDMethod.KEY:ZXGg25NWuhF6qKcx",
    "credential": "cred:94055362-64ea-45bc-a224-73b451a2aeab",
    "verification": "valid",
    "totalTime": "4s"
  }
}
```

## 🔒 Vault Secret Management

### Secret Organization

Secrets are organized in Vault using a hierarchical structure:

```
kv/
├── database/config          # Database connection details
│   ├── host: postgres
│   ├── port: 5432
│   ├── database: dididentity
│   ├── username: postgres
│   └── password: VaultSecureDB2024
├── rabbitmq/config          # RabbitMQ credentials and settings
│   ├── username: admin
│   ├── password: VaultSecureRMQ2024
│   ├── host: rabbitmq
│   └── port: 5672
├── auth/jwt                 # JWT configuration and keys
│   ├── secret_key: [generated]
│   ├── algorithm: HS256
│   └── access_token_expire_minutes: 30
├── grafana/config           # Grafana admin credentials
│   ├── admin_user: admin
│   ├── admin_password: VaultSecureGrafana2024
│   └── secret_key: [generated]
├── security/encryption      # Master encryption keys
│   └── master_key: [generated]
├── monitoring/config        # Monitoring endpoints and settings
│   ├── prometheus_url: http://prometheus:9090
│   └── jaeger_url: http://jaeger:16686
└── services/api_keys        # Service-specific API keys
    ├── auth_service: [generated]
    ├── did_service: [generated]
    ├── credential_service: [generated]
    └── verification_service: [generated]
```

### Accessing Vault

- **Vault UI**: http://localhost:8200 (token: root)
- **CLI Access**: Use `vault` commands with `VAULT_ADDR=http://localhost:8200` and `VAULT_TOKEN=root`
- **Dashboard Integration**: View Vault status in the monitoring dashboard

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

# Get RabbitMQ credentials
vault kv get kv/rabbitmq/config

# Get Grafana credentials  
vault kv get kv/grafana/config
```

For detailed information about the Vault integration, see [vault/VAULT_INTEGRATION.md](vault/VAULT_INTEGRATION.md).

## 📚 API Examples

### Create a User

```bash
curl -X POST http://localhost:8004/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'
```

### Create a DID

```bash
# Get JWT token first
TOKEN=$(curl -X POST http://localhost:8004/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')

# Create DID with authentication
curl -X POST http://localhost:8001/dids \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"key","identifier":"AbCdEfGhIjKlMnOpQrSt"}'
```

### Resolve a DID

```bash
curl http://localhost:8001/dids/did:DIDMethod.KEY:AbCdEfGhIjKlMnOpQrSt
```

### Issue a Credential

```bash
curl -X POST http://localhost:8002/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
    "holder_did": "did:DIDMethod.KEY:AbCdEfGhIjKlMnOpQrSt",
    "credential_data": {
      "name": "John Doe",
      "degree": "Bachelor of Science",
      "institution": "DIDentity University",
      "graduation_year": 2024
    }
  }'
```

### Verify a Credential

```bash
curl -X POST http://localhost:8003/credentials/verify \
  -H "Content-Type: application/json" \
  -d '{"credential_id": "cred:94055362-64ea-45bc-a224-73b451a2aeab"}'
```

## 🚀 Getting Started

### Service Access Points

After starting the services, they will be available at:

- **🖥️ Enhanced Monitoring Dashboard**: http://localhost:8080
  - Real-time service health monitoring
  - Interactive DIDentity workflow testing  
  - Secure access to monitoring tools
  - Comprehensive system status overview

- **🔐 Core Services**:
  - Auth Service: http://localhost:8004/docs
  - DID Service: http://localhost:8001/docs
  - Credential Service: http://localhost:8002/docs
  - Verification Service: http://localhost:8003/docs

- **🛠️ Infrastructure & Monitoring**:
  - RabbitMQ Management: http://localhost:15672 (admin/VaultSecureRMQ2024)
  - Vault UI: http://localhost:8200 (token: root)
  - Grafana: http://localhost:3000 (admin/VaultSecureGrafana2024)
  - Prometheus: http://localhost:9090
  - Jaeger UI: http://localhost:16686

### Basic Usage Flow

1. **Access the Enhanced Monitoring Dashboard** at http://localhost:8080
2. **Test the Complete Workflow** using the "Test Complete DIDentity Workflow" button
3. **Monitor System Health** through the service status cards and monitoring tools
4. **Check Vault Status** and secrets at http://localhost:8200
5. **Explore APIs** using the OpenAPI documentation links

### Accessing Credentials

All service credentials are managed by Vault:

1. **Via Enhanced Dashboard**: View Vault status and health information
2. **Via Vault UI**: Navigate to http://localhost:8200 and browse the `kv/` secrets
3. **Via CLI**: Use vault commands as shown above
4. **Via Monitoring Tools**: Use the secure authentication system in the dashboard

## 📁 Project Structure

```
DIDentity/
├── auth-service/             # Authentication service
│   └── src/                  # Auth service source code with Vault integration
├── did-service/              # DID management service  
│   └── src/                  # DID service source code
├── credential-service/       # Credential service
│   └── src/                  # Credential service source code
├── verification-service/     # Verification service
│   └── src/                  # Verification service source code
├── vault/                    # Vault configuration and integration
│   ├── scripts/              # Vault initialization and configuration scripts
│   │   ├── init_vault.sh     # Vault setup with secure secret generation
│   │   └── configure_services.sh # Service configuration with Vault secrets
│   ├── vault_client.py       # Shared Vault client library with caching
│   └── VAULT_INTEGRATION.md  # Detailed Vault documentation
├── monitoring/               # Monitoring configuration
│   └── grafana/              # Grafana dashboards and config
├── monitoring-dashboard/     # Enhanced unified monitoring dashboard
│   ├── main.py               # FastAPI backend with workflow testing API
│   ├── templates/            # Enhanced dashboard templates
│   │   └── dashboard.html    # Interactive dashboard with sequential workflow
│   └── static/               # Dashboard assets
├── docs/                     # Comprehensive documentation
│   ├── RESTART_RESILIENCE_SOLUTION.md
│   ├── SECURE_MONITORING_GUIDE.md
│   ├── VAULT_DEPLOYMENT_SUMMARY.md
│   └── CODEBASE_CLEANUP_SUMMARY.md
└── docker-compose.yml        # Complete service orchestration with Vault
```

## 🔐 Security Features

### Vault Integration Benefits

- **No Hardcoded Secrets**: All sensitive data managed by Vault with zero hardcoded credentials
- **Automatic Secret Generation**: Secure random passwords using cryptographic methods
- **Centralized Management**: Single point of control for all secrets with hierarchical organization
- **Audit Logging**: Complete trail of secret access and modifications
- **Secret Rotation**: Built-in support for credential rotation and lifecycle management
- **Fallback Mechanisms**: Graceful degradation if Vault unavailable
- **Restart Resilience**: Fixed passwords ensure consistent operation across container restarts

### Enhanced Monitoring Security

- **Session-Based Authentication**: HTTP-only cookies with SameSite protection
- **Zero Credential Exposure**: Credentials never sent to or stored in browser
- **Secure Proxy Architecture**: Server-side request forwarding with pre-authenticated clients
- **Auto-Refresh Support**: Persistent sessions through dashboard auto-refresh
- **Defense in Depth**: Multiple security layers from browser to target service

### Production Considerations

For production deployment:

1. **Use Vault in Production Mode**: Configure with proper storage backend (Consul, etcd)
2. **Implement Auto-Unseal**: Use cloud KMS for automatic unsealing
3. **Set Up Authentication**: Use AppRole or Kubernetes authentication instead of root token
4. **Configure TLS**: Enable TLS for all Vault communication
5. **Backup Strategy**: Implement regular secret backups and disaster recovery
6. **Monitoring**: Set up Vault metrics and alerting with the enhanced dashboard
7. **Network Security**: Implement proper network segmentation and firewall rules

See [vault/VAULT_INTEGRATION.md](vault/VAULT_INTEGRATION.md) for detailed production guidance.

## 🛠️ Development

### Running in Development

The current setup is optimized for development with:
- Vault in development mode with automatic initialization
- Enhanced monitoring dashboard with real-time testing
- Automatic secret initialization and service configuration
- Simplified authentication for rapid development
- Local storage with Docker volumes

### Adding New Secrets

To add new secrets to Vault:

1. Update `vault/scripts/init_vault.sh` to include the new secret
2. Add convenience methods to `vault/vault_client.py`
3. Update services to use the new secret via the Vault client
4. Test using the enhanced monitoring dashboard
5. Document the changes

### Testing Workflow Changes

Use the Enhanced Monitoring Dashboard to test workflow modifications:

1. Access http://localhost:8080
2. Click "Test Complete DIDentity Workflow"
3. Monitor real-time execution and results
4. Use detailed error reporting for troubleshooting





## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the monitoring dashboard for system health
- Use the interactive workflow testing for troubleshooting

---

<div align="center">
<i>DIDentity - ParleSec</i>
</div>
