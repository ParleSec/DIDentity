# DIDentity API Reference

## Overview

Complete reference documentation for the DIDentity decentralized identity platform APIs. The platform consists of four microservices:

- **Auth Service** (Port 8004): User authentication and JWT token management
- **DID Service** (Port 8001): Decentralized identifier operations  
- **Credential Service** (Port 8002): Verifiable credential management
- **Verification Service** (Port 8003): Credential verification and validation

**Important**: This platform uses a custom DID format: `did:DIDMethod.{METHOD}:{identifier}`

## Base URLs

- Auth Service: `http://localhost:8004`
- DID Service: `http://localhost:8001`
- Credential Service: `http://localhost:8002`
- Verification Service: `http://localhost:8003`

## Authentication

Most endpoints require JWT Bearer token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Obtain tokens through the Auth Service registration or login endpoints.

---

## Auth Service API (Port 8004)

### POST /signup

Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john.doe@example.com", 
  "password": "SecurePassword123!"
}
```

**Response (HTTP 200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Response (HTTP 500):**
```json
{
  "detail": "Database connection error"
}
```

### POST /login

Authenticate a user with email and password.

**Request Body (application/x-www-form-urlencoded):**
```
username=john.doe@example.com
password=SecurePassword123!
```

**Response (HTTP 200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Response (HTTP 500):**
```json
{
  "detail": "Database connection error"
}
```

### POST /token

Alternative token endpoint using OAuth2 password flow.

**Request Body (application/x-www-form-urlencoded):**
```
username=john.doe@example.com
password=SecurePassword123!
grant_type=password
```

**Response (HTTP 200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /token/refresh

Refresh an expired access token.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (HTTP 200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /token/revoke

Revoke an access or refresh token.

**Important**: Requires both query parameter and request body with the same token value.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Query Parameters:**
- `token` (required): Token to revoke

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (HTTP 200):**
```json
{
  "message": "Token revoked successfully"
}
```

### GET /health

Check service health status.

**Response (HTTP 200):**
```json
{
  "status": "healthy",
  "database": "connected", 
  "timestamp": "2025-06-11T03:46:17Z"
}
```

### GET /sdk/{language}

Generate client SDK instructions.

**Supported languages:** `typescript`, `python`, `java`

**Response (HTTP 200):**
```json
{
  "message": "SDK for typescript would be generated here",
  "steps": [
    "1. Download the OpenAPI spec from /openapi.json",
    "2. Use an OpenAPI generator tool to create a typescript client", 
    "3. Example command: openapi-generator-cli generate -i openapi.json -g typescript -o ./generated-client"
  ]
}
```

---

## DID Service API (Port 8001)

### POST /dids

Create a new Decentralized Identifier.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "method": "key",
  "identifier": "z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "controller": null
}
```

**Supported DID Methods:**
- `key`: Cryptographic key-based DIDs
- `web`: Web domain-based DIDs  
- `ethr`: Ethereum address-based DIDs
- `sov`: Sovrin network DIDs
- `ion`: ION network DIDs

**Response (HTTP 200):**
```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "verificationMethod": [
    {
      "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
      "publicKeyJwk": null,
      "publicKeyBase58": null,
      "publicKeyMultibase": "zz6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
      "blockchainAccountId": null
    }
  ],
  "authentication": [
    "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1"
  ],
  "assertionMethod": null,
  "keyAgreement": null,
  "capabilityInvocation": null,
  "capabilityDelegation": null,
  "service": null
}
```

**Method-Specific Examples:**

**Web DID Response:**
```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:DIDMethod.WEB:example.com",
  "controller": "did:DIDMethod.WEB:example.com",
  "verificationMethod": [
    {
      "id": "did:DIDMethod.WEB:example.com#keys-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:DIDMethod.WEB:example.com",
      "publicKeyJwk": {
        "kty": "OKP",
        "crv": "Ed25519", 
        "x": "8c443818-b555-4f93-a542-695d76613156"
      },
      "publicKeyBase58": null,
      "publicKeyMultibase": null,
      "blockchainAccountId": null
    }
  ],
  "authentication": [
    "did:DIDMethod.WEB:example.com#keys-1"
  ]
}
```

**Ethereum DID Response:**
```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:DIDMethod.ETHR:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
  "controller": "did:DIDMethod.ETHR:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
  "verificationMethod": [
    {
      "id": "did:DIDMethod.ETHR:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC#keys-1",
      "type": "EcdsaSecp256k1RecoveryMethod2020",
      "controller": "did:DIDMethod.ETHR:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
      "publicKeyJwk": null,
      "publicKeyBase58": null,
      "publicKeyMultibase": null,
      "blockchainAccountId": "eip155:1:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    }
  ],
  "authentication": [
    "did:DIDMethod.ETHR:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC#keys-1"
  ]
}
```

### GET /dids/{did}

Resolve a DID to retrieve its DID Document.

**Path Parameters:**
- `did` (required): URL-encoded DID to resolve

**Example Request:**
```
GET /dids/did%3ADIDMethod.KEY%3Az6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH
```

**Response (HTTP 200) - Successful Resolution:**
```json
{
  "didResolutionMetadata": {
    "contentType": "application/did+json",
    "retrieved": "2025-06-11T03:46:18.506478Z",
    "error": null
  },
  "didDocument": {
    "@context": "https://www.w3.org/ns/did/v1",
    "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
    "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
    "verificationMethod": [
      {
        "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1",
        "type": "Ed25519VerificationKey2020",
        "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
        "publicKeyJwk": null,
        "publicKeyBase58": null,
        "publicKeyMultibase": "zz6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
        "blockchainAccountId": null
      }
    ],
    "authentication": [
      "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1"
    ],
    "assertionMethod": null,
    "keyAgreement": null,
    "capabilityInvocation": null,
    "capabilityDelegation": null,
    "service": null
  },
  "didDocumentMetadata": {
    "created": "2025-06-11T03:46:18.081298+00:00Z",
    "updated": "2025-06-11T03:46:18.081298+00:00Z",
    "deactivated": null,
    "versionId": null
  }
}
```

**Response (HTTP 200) - DID Not Found:**
```json
{
  "didResolutionMetadata": {
    "contentType": "application/did+json",
    "retrieved": "2025-06-11T03:46:19.499965Z",
    "error": "DID not found"
  },
  "didDocument": {
    "id": "did:key:invalid",
    "@context": "https://www.w3.org/ns/did/v1",
    "controller": null,
    "verificationMethod": [],
    "authentication": [],
    "assertionMethod": null,
    "keyAgreement": null,
    "capabilityInvocation": null,
    "capabilityDelegation": null,
    "service": null
  },
  "didDocumentMetadata": {
    "created": null,
    "updated": null,
    "deactivated": null,
    "versionId": null
  }
}
```

### GET /health

Check DID service health status.

**Response (HTTP 200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T03:46:17Z"
}
```

### GET /sdk/{language}

Generate client SDK instructions for DID service.

**Supported languages:** `typescript`, `python`, `java`

**Response (HTTP 200):**
```json
{
  "message": "SDK for python would be generated here",
  "steps": [
    "1. Download the OpenAPI spec from /openapi.json",
    "2. Use an OpenAPI generator tool to create a python client",
    "3. Example command: openapi-generator-cli generate -i openapi.json -g python -o ./generated-client"
  ]
}
```

---

## Credential Service API (Port 8002)

### POST /credentials/issue

Issue a new verifiable credential.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "holder_did": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "credential_data": {
    "@context": [
      "https://www.w3.org/2018/credentials/v1",
      "https://www.w3.org/2018/credentials/examples/v1"
    ],
    "type": ["VerifiableCredential", "UniversityDegreeCredential"],
    "credentialSubject": {
      "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
      "degree": {
        "type": "BachelorDegree",
        "name": "Bachelor of Computer Science",
        "university": "Test University"
      }
    },
    "issuanceDate": "2025-06-11T03:46:18.512045Z"
  }
}
```

**Response (HTTP 200):**
```json
{
  "credential_id": "cred:05e5c7b7-020f-456e-9f47-f20776d4411a"
}
```

**Credential Type Examples:**

**Identity Credential:**
```json
{
  "holder_did": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "credential_data": {
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    "type": ["VerifiableCredential", "IdentityCredential"],
    "credentialSubject": {
      "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
      "name": "Test User",
      "birthDate": "1990-01-01",
      "nationality": "US"
    },
    "issuanceDate": "2025-06-11T03:46:18.512045Z"
  }
}
```

**Professional Credential with Expiration:**
```json
{
  "holder_did": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "credential_data": {
    "@context": [
      "https://www.w3.org/2018/credentials/v1",
      "https://schema.org"
    ],
    "type": ["VerifiableCredential", "ProfessionalCredential"],
    "credentialSubject": {
      "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
      "jobTitle": "Software Engineer",
      "worksFor": {
        "@type": "Organization",
        "name": "Test Corp"
      },
      "skills": ["Python", "API Development", "Testing"]
    },
    "issuanceDate": "2025-06-11T03:46:18.512045Z",
    "expirationDate": "2026-06-11T03:46:18.512045Z"
  }
}
```

**Error Response (HTTP 500):**
```json
{
  "detail": "Database connection error"
}
```

### GET /health

Check credential service health status.

**Response (HTTP 200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T03:46:17Z"
}
```

---

## Verification Service API (Port 8003)

### POST /credentials/verify

Verify the authenticity and validity of a verifiable credential.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "credential_id": "cred:05e5c7b7-020f-456e-9f47-f20776d4411a"
}
```

**Response (HTTP 200) - Valid Credential:**
```json
{
  "status": "valid",
  "credential_data": {
    "type": ["VerifiableCredential", "UniversityDegreeCredential"],
    "@context": [
      "https://www.w3.org/2018/credentials/v1",
      "https://www.w3.org/2018/credentials/examples/v1"
    ],
    "issuanceDate": "2025-06-11T03:46:18.512045Z",
    "credentialSubject": {
      "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
      "degree": {
        "name": "Bachelor of Computer Science",
        "type": "BachelorDegree",
        "university": "Test University"
      }
    }
  },
  "holder_did": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
  "did_document": {
    "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
    "service": null,
    "@context": "https://www.w3.org/ns/did/v1",
    "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
    "keyAgreement": null,
    "authentication": [
      "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1"
    ],
    "assertionMethod": null,
    "verificationMethod": [
      {
        "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1",
        "type": "Ed25519VerificationKey2020",
        "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
        "publicKeyJwk": null,
        "publicKeyBase58": null,
        "publicKeyMultibase": "zz6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
        "blockchainAccountId": null
      }
    ],
    "capabilityDelegation": null,
    "capabilityInvocation": null
  }
}
```

**Error Response (HTTP 500):**
```json
{
  "detail": "Database connection error"
}
```

### GET /health

Check verification service health status.

**Response (HTTP 200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T03:46:17Z"
}
```

---

## Error Handling

All services typically return HTTP 500 for error conditions, including:

- Authentication failures
- Database connection errors  
- Invalid request data
- Resource not found scenarios

**Common Error Response Format:**
```json
{
  "detail": "Database connection error"
}
```

**Best Practices:**
1. Always check for HTTP 200 status code for success
2. Parse the `detail` field from error responses for specific error messages
3. Implement retry logic for network-related errors
4. Handle token expiration by refreshing tokens automatically

---

## DID Format Specification

This platform uses a custom DID format:

**Format:** `did:DIDMethod.{METHOD}:{identifier}`

**Examples:**
- `did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH`
- `did:DIDMethod.WEB:example.com`
- `did:DIDMethod.ETHR:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC`
- `did:DIDMethod.SOV:WRfXPg8dantKVubE3HX8pw`
- `did:DIDMethod.ION:EiClkZMDxPKqC9c-umQfTkR8vvZ9JPhl_xLDI9Ef9Fxn9A`

**Method-Specific Identifier Requirements:**
- **key**: Base58-encoded public key
- **web**: Domain name
- **ethr**: Ethereum address (0x...)
- **sov**: Sovrin-specific identifier  
- **ion**: ION-specific identifier

---

## Rate Limiting

- No explicit rate limiting is currently implemented
- Default token expiration: 1800 seconds (30 minutes)
- Consider implementing client-side request throttling for production use

---

## SDK Availability

SDK generation endpoints are only available for:
- **Auth Service** (port 8004): `/sdk/{language}`
- **DID Service** (port 8001): `/sdk/{language}`

Supported languages: `typescript`, `python`, `java`

Credential and Verification services do not provide SDK endpoints.

---

## Testing

Use the comprehensive test suite to validate API integration:

```bash
cd tests
pip install -r requirements.txt
python comprehensive_api_test.py
```

The test suite covers all 14 documented endpoints with 31 comprehensive test cases and provides detailed request/response logging. 