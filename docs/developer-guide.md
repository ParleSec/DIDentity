# Developer Guide

## Overview
This project implements a decentralized identity solution using microservices, FastAPI, and PostgreSQL.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Start services: `docker-compose up --build`
3. Access services:
   - Authentication: `http://localhost:8000`
   - DID Management: `http://localhost:8001`
   - Credential Service: `http://localhost:8002`
   - Verification Service: `http://localhost:8003`

## Testing
- Unit tests: `pytest tests/unit`
- Integration tests: `pytest tests/integration`
- End-to-end tests: `pytest tests/e2e`

## Monitoring
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`