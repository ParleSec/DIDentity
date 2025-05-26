import requests
import json
import time
import uuid
from typing import Dict, Optional
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IdentityDemo:
    def __init__(self):
        self.base_urls = {
            "auth": "http://localhost:8004",
            "did": "http://localhost:8001",
            "credential": "http://localhost:8002",
            "verification": "http://localhost:8003"
        }
        self.token = None
        self.did = None
        self.credential_id = None

    def _handle_request(self, method: str, url: str, **kwargs) -> Dict:
        """Generic request handler with retries and error handling"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    def register_user(self, username: str, email: str, password: str) -> str:
        """Register a new user and get access token"""
        logger.info("1. Registering new user...")
        try:
            result = self._handle_request(
                "POST",
                f"{self.base_urls['auth']}/signup",
                json={
                    "username": username,
                    "email": email,
                    "password": password
                }
            )
            self.token = result["access_token"]
            logger.info("✓ User registration successful")
            return self.token
        except Exception as e:
            logger.error("✗ User registration failed")
            raise

    def create_did(self) -> str:
        """Create a DID for the registered user"""
        logger.info("\n2. Creating DID...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            # For key method, the identifier needs to be in valid Base58 format
            
            # Simple Base58 character set (no 0, O, I, l)
            base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            random_id = ''.join(random.choice(base58_chars) for _ in range(16))
            
            result = self._handle_request(
                "POST",
                f"{self.base_urls['did']}/dids",
                headers=headers,
                json={
                    "method": "key",
                    "identifier": random_id
                }
            )
            self.did = result["id"]
            logger.info(f"✓ DID created: {self.did}")
            return self.did
        except Exception as e:
            logger.error("✗ DID creation failed")
            raise

    def issue_credential(self, credential_data: Dict) -> str:
        """Issue a verifiable credential"""
        logger.info("\n3. Issuing credential...")
        try:
            result = self._handle_request(
                "POST",
                f"{self.base_urls['credential']}/credentials/issue",
                json={
                    "holder_did": self.did,
                    "credential_data": credential_data
                }
            )
            self.credential_id = result["credential_id"]
            logger.info(f"✓ Credential issued: {self.credential_id}")
            return self.credential_id
        except Exception as e:
            logger.error("✗ Credential issuance failed")
            raise

    def verify_credential(self) -> Dict:
        """Verify the issued credential"""
        logger.info("\n4. Verifying credential...")
        try:
            result = self._handle_request(
                "POST",
                f"{self.base_urls['verification']}/credentials/verify",
                json={
                    "credential_id": self.credential_id
                }
            )
            logger.info("✓ Credential verification successful")
            return result
        except Exception as e:
            logger.error("✗ Credential verification failed")
            raise

    def run_demo(self):
        """Run the complete demo flow"""
        try:
            # Generate a random email to avoid conflicts
            random_id = str(uuid.uuid4())[:8]
            
            # Step 1: Register User
            self.register_user(
                username="User" + random_id,
                email=f"user_{random_id}@example.com",
                password="SecurePassword123"
            )

            # Step 2: Create DID
            self.create_did()

            # Step 3: Issue Credential
            self.issue_credential({
                "name": "Walter White",
                "degree": "Bachelor of Chemistry",
                "university": "Albert University",
                "graduationYear": "1994",
                "honors": "Cum Laude"
            })

            # Step 4: Verify Credential
            verification_result = self.verify_credential()

            logger.info("\n✓ Demo completed successfully!")
            return {
                "token": self.token,
                "did": self.did,
                "credential_id": self.credential_id,
                "verification_result": verification_result
            }

        except Exception as e:
            logger.error(f"\n✗ Demo failed: {str(e)}")
            raise

def main():
    demo = IdentityDemo()
    try:
        results = demo.run_demo()
        logger.info("\nDemo Results:")
        logger.info(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()