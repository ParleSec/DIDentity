# DIDentity API Integration Guide

## Overview

This guide provides practical examples and step-by-step instructions for integrating with the DIDentity platform APIs. The platform consists of four microservices that work together to provide a complete decentralized identity solution.

**Important**: This platform uses a custom DID format: `did:DIDMethod.{METHOD}:{identifier}`

## Quick Start

### 1. Authentication Flow

Before interacting with most endpoints, you need to authenticate and obtain access tokens.

```bash
# Register a new user
curl -X POST http://localhost:8004/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john.doe@example.com",
    "password": "SecurePassword123!"
  }'

# Response (HTTP 200):
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 1800
# }
```

### 2. Complete Workflow Example

Here's a complete workflow showing how to create a DID, issue a credential, and verify it:

#### Step 1: Create a DID

```bash
# Create a DID using the access token from registration
export ACCESS_TOKEN="your_access_token_here"

curl -X POST http://localhost:8001/dids \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "key",
    "identifier": "z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
    "controller": null
  }'

# Response (HTTP 200):
# {
#   "@context": "https://www.w3.org/ns/did/v1",
#   "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#   "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#   "verificationMethod": [
#     {
#       "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1",
#       "type": "Ed25519VerificationKey2020",
#       "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#       "publicKeyMultibase": "zz6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#       "publicKeyJwk": null,
#       "publicKeyBase58": null,
#       "blockchainAccountId": null
#     }
#   ],
#   "authentication": [
#     "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH#keys-1"
#   ],
#   "assertionMethod": null,
#   "keyAgreement": null,
#   "capabilityInvocation": null,
#   "capabilityDelegation": null,
#   "service": null
# }
```

#### Step 2: Issue a Credential

```bash
# Issue a verifiable credential
curl -X POST http://localhost:8002/credentials/issue \
  -H "Content-Type: application/json" \
  -d '{
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
  }'

# Response (HTTP 200):
# {
#   "credential_id": "cred:05e5c7b7-020f-456e-9f47-f20776d4411a"
# }
```

#### Step 3: Verify the Credential

```bash
# Verify the issued credential
curl -X POST http://localhost:8003/credentials/verify \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "cred:05e5c7b7-020f-456e-9f47-f20776d4411a"
  }'

# Response (HTTP 200):
# {
#   "status": "valid",
#   "credential_data": {
#     "type": ["VerifiableCredential", "UniversityDegreeCredential"],
#     "@context": [
#       "https://www.w3.org/2018/credentials/v1",
#       "https://www.w3.org/2018/credentials/examples/v1"
#     ],
#     "issuanceDate": "2025-06-11T03:46:18.512045Z",
#     "credentialSubject": {
#       "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#       "degree": {
#         "name": "Bachelor of Computer Science",
#         "type": "BachelorDegree",
#         "university": "Test University"
#       }
#     }
#   },
#   "holder_did": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#   "did_document": {
#     "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#     "@context": "https://www.w3.org/ns/did/v1",
#     "controller": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
#     "verificationMethod": [...],
#     "authentication": [...]
#   }
# }
```

## Service-Specific Integration

### Auth Service (Port 8004)

The Auth Service handles user registration, authentication, and token management.

#### User Registration

```javascript
// JavaScript/Node.js example
const registerUser = async (userData) => {
  const response = await fetch('http://localhost:8004/signup', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: userData.username,
      email: userData.email,
      password: userData.password
    })
  });

  if (!response.ok) {
    const error = await response.json();
    // Note: API typically returns HTTP 500 for errors
    throw new Error(error.detail || 'Registration failed');
  }

  return await response.json();
};

// Usage
try {
  const tokens = await registerUser({
    username: 'john_doe',
    email: 'john.doe@example.com',
    password: 'SecurePassword123!'
  });
  
  console.log('Access Token:', tokens.access_token);
  console.log('Refresh Token:', tokens.refresh_token);
} catch (error) {
  console.error('Registration failed:', error.message);
}
```

#### Token Refresh

```python
# Python example
import requests
import time

class AuthClient:
    def __init__(self, base_url="http://localhost:8004"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    def refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        response = requests.post(
            f"{self.base_url}/token/refresh",
            json={"refresh_token": self.refresh_token}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.token_expires_at = time.time() + tokens["expires_in"]
            if tokens.get("refresh_token"):
                self.refresh_token = tokens["refresh_token"]
            return tokens
        else:
            # API typically returns HTTP 500 for errors
            error_detail = response.json().get('detail', 'Token refresh failed')
            raise Exception(f"Token refresh failed: {error_detail}")

    def get_headers(self):
        """Get authorization headers, refreshing token if needed"""
        if self.token_expires_at and time.time() >= self.token_expires_at - 60:
            self.refresh_access_token()
        
        return {"Authorization": f"Bearer {self.access_token}"}
```

#### Token Revocation

**Important**: Token revocation requires both query parameter and request body with the same token value:

```python
def revoke_token(self):
    """Revoke the current access token"""
    if not self.access_token:
        raise ValueError("No access token to revoke")
    
    response = requests.post(
        f"{self.base_url}/token/revoke",
        headers={"Authorization": f"Bearer {self.access_token}"},
        params={"token": self.access_token},  # Required: query parameter
        json={"token": self.access_token}     # Required: request body
    )
    
    if response.status_code == 200:
        result = response.json()
        print(result["message"])  # "Token revoked successfully"
        self.access_token = None
        self.refresh_token = None
        return result
    else:
        error_detail = response.json().get('detail', 'Token revocation failed')
        raise Exception(f"Token revocation failed: {error_detail}")
```

### DID Service (Port 8001)

The DID Service creates and resolves decentralized identifiers using the custom format `did:DIDMethod.{METHOD}:{identifier}`.

#### Creating DIDs

```typescript
// TypeScript example
interface DIDCreateRequest {
  method: 'key' | 'web' | 'ethr' | 'sov' | 'ion';
  identifier: string;
  controller?: string | null;
}

interface DIDDocument {
  '@context': string;
  id: string;
  controller: string;
  verificationMethod: VerificationMethod[];
  authentication: string[];
  assertionMethod?: string[] | null;
  keyAgreement?: string[] | null;
  capabilityInvocation?: string[] | null;
  capabilityDelegation?: string[] | null;
  service?: ServiceEndpoint[] | null;
}

class DIDClient {
  constructor(private baseUrl: string = 'http://localhost:8001') {}

  async createDID(
    request: DIDCreateRequest, 
    accessToken: string
  ): Promise<DIDDocument> {
    const response = await fetch(`${this.baseUrl}/dids`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'DID creation failed');
    }

    return await response.json();
  }

  async resolveDID(did: string): Promise<DIDResolution> {
    // URL encode the DID
    const encodedDID = encodeURIComponent(did);
    
    const response = await fetch(`${this.baseUrl}/dids/${encodedDID}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`DID resolution failed: ${response.status}`);
    }

    return await response.json();
  }
}

// Usage examples for different DID methods
const didClient = new DIDClient();

// Key-based DID
const keyDID = await didClient.createDID({
  method: 'key',
  identifier: 'z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH',
  controller: null
}, accessToken);
// Result: did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH

// Web-based DID
const webDID = await didClient.createDID({
  method: 'web',
  identifier: 'example.com',
  controller: null
}, accessToken);
// Result: did:DIDMethod.WEB:example.com

// Ethereum-based DID
const ethrDID = await didClient.createDID({
  method: 'ethr',
  identifier: '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
  controller: null
}, accessToken);
// Result: did:DIDMethod.ETHR:0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
```

#### DID Resolution

```go
// Go example
package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "strings"
)

type DIDResolution struct {
    DIDResolutionMetadata DIDResolutionMetadata `json:"didResolutionMetadata"`
    DIDDocument           DIDDocument           `json:"didDocument"`
    DIDDocumentMetadata   DIDDocumentMetadata   `json:"didDocumentMetadata"`
}

type DIDResolutionMetadata struct {
    ContentType string  `json:"contentType"`
    Retrieved   string  `json:"retrieved"`
    Error       *string `json:"error"`
}

func ResolveDID(did string) (*DIDResolution, error) {
    // URL encode the DID
    encodedDID := url.QueryEscape(did)
    
    resp, err := http.Get(fmt.Sprintf("http://localhost:8001/dids/%s", encodedDID))
    if err != nil {
        return nil, fmt.Errorf("request failed: %w", err)
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, fmt.Errorf("failed to read response: %w", err)
    }

    var resolution DIDResolution
    if err := json.Unmarshal(body, &resolution); err != nil {
        return nil, fmt.Errorf("failed to parse response: %w", err)
    }

    // Check if resolution has an error
    if resolution.DIDResolutionMetadata.Error != nil {
        return &resolution, fmt.Errorf("DID resolution error: %s", *resolution.DIDResolutionMetadata.Error)
    }

    return &resolution, nil
}

// Usage
func main() {
    did := "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH"
    
    resolution, err := ResolveDID(did)
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    fmt.Printf("Resolved DID: %s\n", resolution.DIDDocument.ID)
    fmt.Printf("Controller: %s\n", resolution.DIDDocument.Controller)
    fmt.Printf("Created: %s\n", resolution.DIDDocumentMetadata.Created)
}
```

### Credential Service (Port 8002)

```python
# Python example for credential issuance
import requests
from datetime import datetime, timezone
from typing import Dict, Any

class CredentialClient:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
    
    def issue_credential(
        self, 
        holder_did: str, 
        credential_data: Dict[str, Any]
    ) -> str:
        """Issue a verifiable credential"""
        response = requests.post(
            f"{self.base_url}/credentials/issue",
            json={
                "holder_did": holder_did,
                "credential_data": credential_data
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["credential_id"]
        else:
            error_detail = response.json().get('detail', 'Credential issuance failed')
            raise Exception(f"Credential issuance failed: {error_detail}")

# Usage examples for different credential types
client = CredentialClient()

# Education credential
education_credential = {
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
    "issuanceDate": datetime.now(timezone.utc).isoformat()
}

credential_id = client.issue_credential(
    holder_did="did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
    credential_data=education_credential
)
print(f"Issued credential: {credential_id}")

# Identity credential
identity_credential = {
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    "type": ["VerifiableCredential", "IdentityCredential"],
    "credentialSubject": {
        "id": "did:DIDMethod.KEY:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
        "name": "Test User",
        "birthDate": "1990-01-01",
        "nationality": "US"
    },
    "issuanceDate": datetime.now(timezone.utc).isoformat()
}

# Professional credential with expiration
from datetime import timedelta

professional_credential = {
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
    "issuanceDate": datetime.now(timezone.utc).isoformat(),
    "expirationDate": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
}
```

### Verification Service (Port 8003)

```javascript
// JavaScript example for credential verification
class VerificationClient {
    constructor(baseUrl = 'http://localhost:8003') {
        this.baseUrl = baseUrl;
    }

    async verifyCredential(credentialId) {
        const response = await fetch(`${this.baseUrl}/credentials/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                credential_id: credentialId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Verification failed');
        }

        return await response.json();
    }
}

// Usage
const verificationClient = new VerificationClient();

try {
    const result = await verificationClient.verifyCredential(
        'cred:05e5c7b7-020f-456e-9f47-f20776d4411a'
    );
    
    console.log('Verification Status:', result.status);
    console.log('Holder DID:', result.holder_did);
    console.log('Credential Data:', result.credential_data);
    
    if (result.status === 'valid') {
        console.log('✅ Credential is valid');
        console.log('DID Document:', result.did_document);
    } else {
        console.log('❌ Credential is invalid:', result.error);
    }
} catch (error) {
    console.error('Verification failed:', error.message);
}
```

## Error Handling

The DIDentity platform typically returns HTTP 500 for most error conditions, including:

- Invalid credentials during authentication
- Database connection errors
- Duplicate email registration
- Invalid credential verification requests

### Error Response Format

```json
{
  "detail": "Database connection error"
}
```

### Best Practices for Error Handling

```python
import requests
from typing import Optional

def handle_api_error(response: requests.Response) -> str:
    """Extract error message from API response"""
    try:
        error_data = response.json()
        return error_data.get('detail', f'HTTP {response.status_code} error')
    except ValueError:
        return f'HTTP {response.status_code}: {response.text[:100]}'

def safe_api_call(url: str, method: str = 'GET', **kwargs) -> Optional[dict]:
    """Make API call with proper error handling"""
    try:
        response = requests.request(method, url, **kwargs)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = handle_api_error(response)
            print(f"API Error: {error_msg}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network Error: {str(e)}")
        return None
    except ValueError as e:
        print(f"JSON Parse Error: {str(e)}")
        return None
```

## SDK Generation

SDK generation endpoints are only available for Auth Service (port 8004) and DID Service (port 8001):

```bash
# Get TypeScript SDK instructions for Auth Service
curl http://localhost:8004/sdk/typescript

# Get Python SDK instructions for DID Service  
curl http://localhost:8001/sdk/python

# Get Java SDK instructions
curl http://localhost:8004/sdk/java
```

## Health Checks

Monitor service health across all services:

```bash
# Check all services
for port in 8001 8002 8003 8004; do
    echo "Checking service on port $port..."
    curl -s http://localhost:$port/health | jq '.'
done
```

## Testing Your Integration

Use the comprehensive test suite provided with the platform to validate your integration:

```bash
# Navigate to tests directory
cd tests

# Install dependencies
pip install -r requirements.txt

# Run comprehensive tests
python comprehensive_api_test.py
```

This will run 31 tests covering all endpoints and provide detailed request/response logging to help debug any integration issues.

## Rate Limiting and Performance

- Default token expiration: 1800 seconds (30 minutes)
- No explicit rate limiting implemented
- Services run on uvicorn with standard performance characteristics
- Consider implementing client-side token caching and refresh logic

## Security Considerations

1. **Token Security**: Store access and refresh tokens securely
2. **HTTPS**: Use HTTPS in production environments
3. **Token Expiration**: Implement proper token refresh logic
4. **DID Format**: Be aware of the custom DID format used by this platform
5. **Error Information**: Error responses may contain sensitive information in development

## Next Steps

1. Set up your development environment
2. Test the authentication flow
3. Create your first DID
4. Issue and verify a test credential
5. Implement proper error handling
6. Consider SDK generation for your preferred language