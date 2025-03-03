# Decentralized Identity Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.1-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg?logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-20.10.8+-2496ED.svg?logo=docker)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat)](https://pycqa.github.io/isort/)

A microservices-based Decentralized Identity (DID) management system that enables secure identity creation, credential issuance, and verification.

## 🌟 Features

- **User Authentication**: Secure user registration and JWT-based authentication
- **DID Management**: Create and manage Decentralized Identifiers
- **Credential Issuance**: Issue verifiable credentials linked to DIDs
- **Credential Verification**: Verify the authenticity of issued credentials
- **Microservices Architecture**: Scalable and maintainable service separation
- **Docker Integration**: Easy deployment with containerization
- **Database Integration**: PostgreSQL for reliable data storage
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: PostgreSQL 17
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker & Docker Compose
- **Documentation**: OpenAPI (Swagger)
- **Monitoring**: Prometheus & Grafana

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.9 or higher
- PostgreSQL 17

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ParleSec/DIDentity
cd DIDentity
```

2. Create a `.env` file:
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=decentralized_id
DATABASE_URL=postgresql://postgres:password@db:5432/decentralized_id
SECRET_KEY=your-secret-key-here
```

3. Build and start the services:
```bash
docker-compose up -d
```

4. Verify all services are running:
```bash
docker-compose ps
```

### Running the Demo

Test the complete flow using the provided demo script:
```bash
python demo.py
```

## 📚 API Documentation

After starting the services, access the API documentation at:
- Auth Service: `http://localhost:8004/docs`
- DID Service: `http://localhost:8001/docs`
- Credential Service: `http://localhost:8002/docs`
- Verification Service: `http://localhost:8003/docs`

## 🏗️ Architecture

The system consists of four microservices:

1. **Auth Service** (Port 8004)
   - User registration and authentication
   - JWT token generation and validation

2. **DID Service** (Port 8001)
   - DID creation and management
   - DID document storage and retrieval

3. **Credential Service** (Port 8002)
   - Credential issuance
   - Credential storage and management

4. **Verification Service** (Port 8003)
   - Credential verification
   - DID and credential validation

## 🔍 Testing

Run the test suite:
```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# End-to-end tests
pytest tests/e2e
```

## 📊 Monitoring

Access monitoring dashboards:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## 🛡️ Security Features

- Password hashing with bcrypt
- JWT-based authentication
- Database connection pooling
- CORS middleware
- Input validation
- Error handling and logging

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
