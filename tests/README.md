# DIDentity Comprehensive API Test Suite

This directory contains a complete test suite that validates **every single documented endpoint** across all DIDentity platform services.

## 🎯 What Gets Tested

### Complete API Coverage

The test suite validates all documented endpoints from the [API Documentation](../docs/api-documentation.yaml):

#### Auth Service (Port 8004)
- ✅ `POST /signup` - User registration
- ✅ `POST /login` - User authentication
- ✅ `POST /token` - Alternative token endpoint
- ✅ `POST /token/refresh` - Token refresh
- ✅ `POST /token/revoke` - Token revocation
- ✅ `GET /health` - Health check
- ✅ `GET /sdk/{language}` - SDK generation (typescript, python, java)

#### DID Service (Port 8001)
- ✅ `POST /dids` - DID creation for all methods:
  - `key` method (cryptographic keys)
  - `web` method (web domains)
  - `ethr` method (Ethereum addresses)
  - `sov` method (Sovrin network)
  - `ion` method (ION network)
- ✅ `GET /dids/{did}` - DID resolution
- ✅ `GET /health` - Health check
- ✅ `GET /sdk/{language}` - SDK generation

#### Credential Service (Port 8002)
- ✅ `POST /credentials/issue` - Credential issuance for multiple types:
  - Education credentials
  - Identity credentials
  - Professional credentials
- ✅ `GET /health` - Health check
- ✅ `GET /sdk/{language}` - SDK generation

#### Verification Service (Port 8003)
- ✅ `POST /credentials/verify` - Credential verification
- ✅ `GET /health` - Health check
- ✅ `GET /sdk/{language}` - SDK generation

### Error Scenario Testing

The suite also tests error conditions:
- ✅ Duplicate user registration (400 error)
- ✅ Invalid login credentials (401 error)
- ✅ Invalid DID resolution (404 error)
- ✅ Invalid credential verification (404 error)

### End-to-End Workflow Testing

Tests the complete workflow:
1. User registration → 2. DID creation → 3. Credential issuance → 4. Credential verification

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
cd tests
chmod +x run_comprehensive_test.sh
./run_comprehensive_test.sh
```

**Windows:**
```cmd
cd tests
run_comprehensive_test.bat
```

### Option 2: Manual Setup

1. **Install Dependencies:**
   ```bash
   cd tests
   pip install -r requirements.txt
   ```

2. **Run Tests:**
   ```bash
   python comprehensive_api_test.py
   ```

## 📋 Prerequisites

### Required Services
Ensure all DIDentity services are running:

```bash
# Start all services
docker-compose up -d

# Verify services are running
curl http://localhost:8004/health  # Auth Service
curl http://localhost:8001/health  # DID Service  
curl http://localhost:8002/health  # Credential Service
curl http://localhost:8003/health  # Verification Service
```

### Python Requirements
- Python 3.7+
- Dependencies listed in `requirements.txt`

## 📊 Test Output

The test suite provides detailed, color-coded output:

```
🚀 DIDentity Comprehensive API Test Suite
==============================================================

📊 HEALTH CHECKS
✅ Auth Service Health
✅ Did Service Health
✅ Credential Service Health
✅ Verification Service Health

🔐 AUTHENTICATION TESTS
✅ User Registration
✅ User Login
✅ Token Endpoint
✅ Token Refresh

🆔 DID SERVICE TESTS
✅ Create DID - KEY Method
✅ Create DID - WEB Method
✅ Create DID - ETHR Method
✅ Create DID - SOV Method
✅ Create DID - ION Method
✅ Resolve DID

📄 CREDENTIAL SERVICE TESTS
✅ Issue Credential - Education
✅ Issue Credential - Identity
✅ Issue Credential - Professional

✅ VERIFICATION SERVICE TESTS
✅ Verify Credential

🛠️ SDK GENERATION TESTS
✅ SDK Generation - Auth (typescript)
✅ SDK Generation - Auth (python)
✅ SDK Generation - Auth (java)
... (all service/language combinations)

🚨 Testing Error Scenarios
✅ Invalid Registration (Duplicate Email)
✅ Invalid Login (Wrong Password)
✅ Invalid DID Resolution
✅ Invalid Credential Verification

🔒 FINAL AUTHENTICATION TESTS
✅ Token Revoke

============================================================
TEST SUMMARY
============================================================
Total Tests: 45
Passed: 45
Failed: 0
Success Rate: 100.0%
Duration: 12.34s

🎉 ALL TESTS PASSED!
```

## 🔧 Test Configuration

### Base URLs
The test suite connects to services on localhost:

```python
base_urls = {
    'auth': 'http://localhost:8004',
    'did': 'http://localhost:8001',
    'credential': 'http://localhost:8002',
    'verification': 'http://localhost:8003'
}
```

### Test Data
Each test run uses unique test data:
- Random username: `test_user_{8_chars}`
- Random email: `test_{8_chars}@example.com`
- Fixed password: `TestPassword123!`

## 🎯 Test Coverage Details

### Authentication Flow
1. **Registration**: Creates new user account
2. **Login**: Validates credentials
3. **Token Operations**: Tests refresh and revocation
4. **Authorization**: Uses JWT tokens for protected endpoints

### DID Methods Testing
Tests all 5 supported DID methods with realistic identifiers:

| Method | Test Identifier | Description |
|--------|----------------|-------------|
| `key` | `z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH` | Base58 public key |
| `web` | `example.com` | Domain name |
| `ethr` | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` | Ethereum address |
| `sov` | `WRfXPg8dantKVubE3HX8pw` | Sovrin identifier |
| `ion` | `EiClkZMDxPKqC9c-umQfTkR8vvZ9JPhl_xLDI9Ef9Fxn9A` | ION identifier |

### Credential Types Testing
Tests multiple W3C-compliant credential types:

1. **Education Credential**
   - Type: `UniversityDegreeCredential`
   - Contains: degree information, university details

2. **Identity Credential**
   - Type: `IdentityCredential`
   - Contains: personal information, nationality

3. **Professional Credential**
   - Type: `ProfessionalCredential`
   - Contains: job title, organization, skills, expiration

### SDK Generation Testing
Tests SDK generation for all combinations:
- **Services**: auth, did, credential, verification
- **Languages**: typescript, python, java
- **Total**: 12 SDK generation tests

## 🐛 Troubleshooting

### Common Issues

1. **Services Not Running**
   ```
   ❌ Auth Service Health
   Error: Request failed: Connection refused
   ```
   **Solution**: Start services with `docker-compose up -d`

2. **Permission Denied**
   ```
   bash: ./run_comprehensive_test.sh: Permission denied
   ```
   **Solution**: `chmod +x run_comprehensive_test.sh`

3. **Python Not Found**
   ```
   ❌ Python 3 is required but not installed.
   ```
   **Solution**: Install Python 3.7+ from [python.org](https://python.org)

4. **Dependencies Missing**
   ```
   ModuleNotFoundError: No module named 'requests'
   ```
   **Solution**: Install dependencies with `pip install -r requirements.txt`

### Debug Mode

For detailed debugging, modify the test script to include verbose output:

```python
# Add at the top of comprehensive_api_test.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Considerations

- **Test Duration**: ~10-15 seconds for full suite
- **Parallel Execution**: Tests run sequentially to maintain state
- **Resource Usage**: Minimal - only HTTP requests
- **Cleanup**: No persistent data created (unique test users)

## 🔄 Continuous Integration

This test suite is perfect for CI/CD pipelines:

```yaml
# Example GitHub Actions usage
- name: Run API Tests
  run: |
    cd tests
    python comprehensive_api_test.py
```

The script exits with code 0 for success, 1 for failure.

## 📝 Adding New Tests

To add tests for new endpoints:

1. **Add to the appropriate service section**
2. **Follow the existing pattern**
3. **Update the test count expectations**
4. **Add error scenario testing if applicable**

Example:
```python
def test_new_endpoint(self):
    self.log_test("New Endpoint", "POST /new-endpoint")
    # ... test implementation
    self.result.add_result("New Endpoint", success, error)
```

## 🤝 Contributing

When modifying the test suite:
1. Ensure all existing tests still pass
2. Add appropriate error handling
3. Update this README if adding new test categories
4. Test on both Unix and Windows systems

---

**Total Test Coverage**: 45+ individual tests covering every documented endpoint plus error scenarios and complete workflow validation. 