import pytest
import requests
import time

class TestCompleteFlow:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.base_urls = {
            "auth": "http://localhost:8004",
            "did": "http://localhost:8001",
            "credential": "http://localhost:8002",
            "verification": "http://localhost:8003"
        }
        self.test_user = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123"
        }

    def test_complete_identity_flow(self):
        # 1. Register user
        register_response = requests.post(
            f"{self.base_urls['auth']}/signup",
            json=self.test_user
        )
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]

        # 2. Create DID
        did_response = requests.post(
            f"{self.base_urls['did']}/dids",
            json={"method": "key", "identifier": f"test_{int(time.time())}"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert did_response.status_code == 200
        did = did_response.json()["id"]

        # 3. Issue credential
        credential_data = {
            "holder_did": did,
            "credential_data": {
                "name": "Test User",
                "degree": "Bachelor of Science",
                "university": "Test University"
            }
        }
        issue_response = requests.post(
            f"{self.base_urls['credential']}/credentials/issue",
            json=credential_data
        )
        assert issue_response.status_code == 200
        credential_id = issue_response.json()["credential_id"]

        # 4. Verify credential
        verify_response = requests.post(
            f"{self.base_urls['verification']}/credentials/verify",
            json={"credential_id": credential_id}
        )
        assert verify_response.status_code == 200
        verification_result = verify_response.json()
        assert verification_result["status"] == "valid"
        assert verification_result["holder_did"] == did