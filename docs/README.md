# DIDentity Documentation

This directory contains comprehensive documentation for the DIDentity decentralized identity platform.

## 📚 Documentation Overview

### API Documentation

- **[Complete API Specification](api-documentation.yaml)** - Full OpenAPI 3.0 specification covering all services
- **[API Reference Guide](api-reference.md)** - Detailed endpoint documentation with examples
- **[API Integration Guide](api-integration-guide.md)** - Practical implementation examples and best practices

### Developer Resources

- **[Developer Guide](developer-guide.md)** - Basic development setup and testing

## 🚀 Quick Start

### 1. API Reference
Start with the [API Reference Guide](api-reference.md) for:
- Complete endpoint documentation
- Request/response examples
- Authentication requirements
- Error handling

### 2. Integration Examples
See the [API Integration Guide](api-integration-guide.md) for:
- Multi-language code examples
- Complete workflow implementations
- Error handling patterns
- Performance optimization

### 3. OpenAPI Specification
Use the [API Specification](api-documentation.yaml) for:
- SDK generation
- API testing tools
- Documentation generators
- Contract testing

## 📖 Documentation Structure

### API Services Coverage

| Service | Port | Documentation Coverage |
|---------|------|----------------------|
| **Auth Service** | 8004 | ✅ Complete - Registration, login, token management |
| **DID Service** | 8001 | ✅ Complete - DID creation, resolution, all methods |
| **Credential Service** | 8002 | ✅ Complete - Credential issuance, multiple types |
| **Verification Service** | 8003 | ✅ Complete - Credential verification, validation |

### Key Features Documented

- **Authentication Flow** - JWT token management and refresh
- **DID Methods** - Support for key, web, ethr, sov, ion methods
- **Credential Types** - Education, identity, professional credentials
- **Error Handling** - Comprehensive error scenarios and responses
- **Rate Limiting** - Service limits and best practices
- **SDK Generation** - Multi-language client generation

## 🛠️ Using the Documentation

### For Developers

1. **Quick Integration**: Start with the curl examples in the API Reference
2. **Language-Specific**: Check the Integration Guide for your language
3. **SDK Generation**: Use the OpenAPI spec with code generators

### For Testing

```bash
# Test the complete workflow
curl -X POST http://localhost:8004/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "password123"}'
```

### For SDK Generation

```bash
# Generate TypeScript SDK
openapi-generator-cli generate \
  -i docs/api-documentation.yaml \
  -g typescript-axios \
  -o ./generated-sdk
```

## 🔗 Related Resources

- **Main README**: [../README.md](../README.md) - Project overview and setup
- **Interactive Demo**: [../interactive_demo.py](../interactive_demo.py) - GUI-based testing
- **Docker Setup**: [../docker-compose.yml](../docker-compose.yml) - Service configuration

## 📝 Contributing to Documentation

When updating the API documentation:

1. Update the OpenAPI specification first
2. Reflect changes in the Reference Guide
3. Add examples to the Integration Guide
4. Update this README if new files are added

## 🔍 Finding What You Need

| I want to... | Go to... |
|-------------|----------|
| Understand all endpoints | [API Reference](api-reference.md) |
| See code examples | [Integration Guide](api-integration-guide.md) |
| Generate an SDK | [OpenAPI Spec](api-documentation.yaml) |
| Set up development | [Developer Guide](developer-guide.md) |
| Test the API | [Integration Guide - Testing Section](api-integration-guide.md#testing-your-integration) |

---

**Note**: This documentation is automatically tested against the live services. All examples and code snippets are verified to work with the current implementation. 