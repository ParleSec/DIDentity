import requests
import json
import os
from typing import Dict, Any, Optional
import streamlit as st

class DIDentityClient:
    def __init__(self):
        # Detect if running in Docker environment
        is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV') == 'true'
        
        if is_docker:
            # Docker service URLs (internal network communication)
            self.base_urls = {
                "auth": "http://auth-service:8000",
                "did": "http://did-service:8000", 
                "credential": "http://credential-service:8000",
                "verification": "http://verification-service:8000"
            }
        else:
            # Local development URLs (external ports)
            self.base_urls = {
                "auth": "http://localhost:8004",
                "did": "http://localhost:8001", 
                "credential": "http://localhost:8002",
                "verification": "http://localhost:8003"
            }
        
        # Default headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(self, method: str, service: str, endpoint: str, data: Dict = None, 
                     auth_required: bool = False) -> Dict[str, Any]:
        """Make HTTP request to a service"""
        url = f"{self.base_urls[service]}{endpoint}"
        headers = self.headers.copy()
        
        # Add auth header if required and available
        if auth_required and hasattr(st.session_state, 'access_token') and st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle response
            if response.status_code >= 400:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                raise Exception(f"API Error ({response.status_code}): {error_detail}")
            
            return response.json() if response.text else {}
            
        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to {service} service at {url}. Make sure the service is running.")
        except requests.exceptions.Timeout:
            raise Exception(f"Request to {service} service timed out.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    # Auth Service Methods
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        return self._make_request("POST", "auth", "/signup", data)
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and get access token"""
        # Use form data for OAuth2PasswordRequestForm compatibility
        data = {
            "username": username,
            "password": password
        }
        
        # For login, we need to send as form data, not JSON
        url = f"{self.base_urls['auth']}/login"
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if response.status_code >= 400:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                raise Exception(f"Login failed ({response.status_code}): {error_detail}")
            
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to auth service. Make sure it's running.")
        except requests.exceptions.Timeout:
            raise Exception("Login request timed out.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Login request failed: {str(e)}")
    
    def revoke_token(self, token: str) -> Dict[str, Any]:
        """Revoke an access token"""
        data = {"token": token}
        return self._make_request("POST", "auth", "/token/revoke", data, auth_required=True)
    
    def get_auth_health(self) -> Dict[str, Any]:
        """Get auth service health status"""
        return self._make_request("GET", "auth", "/health")
    
    # DID Service Methods
    def create_did(self, method: str, controller: Optional[str] = None) -> Dict[str, Any]:
        """Create a new DID"""
        data = {"method": method}
        if controller:
            data["controller"] = controller
        
        return self._make_request("POST", "did", "/dids", data, auth_required=True)
    
    def resolve_did(self, did: str) -> Dict[str, Any]:
        """Resolve a DID to get its document"""
        endpoint = f"/dids/{did}"
        return self._make_request("GET", "did", endpoint, auth_required=True)
    
    def get_did_health(self) -> Dict[str, Any]:
        """Get DID service health status"""
        return self._make_request("GET", "did", "/health")
    
    # Credential Service Methods
    def issue_credential(self, holder_did: str, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Issue a verifiable credential"""
        data = {
            "holder_did": holder_did,
            "credential_data": credential_data
        }
        return self._make_request("POST", "credential", "/credentials/issue", data, auth_required=True)
    
    def get_credential_health(self) -> Dict[str, Any]:
        """Get credential service health status"""
        return self._make_request("GET", "credential", "/health")
    
    # Verification Service Methods
    def verify_credential(self, credential_id: str) -> Dict[str, Any]:
        """Verify a credential"""
        data = {"credential_id": credential_id}
        return self._make_request("POST", "verification", "/credentials/verify", data, auth_required=True)
    
    def get_verification_health(self) -> Dict[str, Any]:
        """Get verification service health status"""
        return self._make_request("GET", "verification", "/health")
    
    # Utility Methods
    def check_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all services"""
        health_results = {}
        
        services = [
            ("auth", self.get_auth_health),
            ("did", self.get_did_health),
            ("credential", self.get_credential_health),
            ("verification", self.get_verification_health)
        ]
        
        for service_name, health_method in services:
            try:
                health_results[service_name] = {
                    "status": "healthy",
                    "data": health_method()
                }
            except Exception as e:
                health_results[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_results
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about all services"""
        return {
            "services": {
                "auth-service": {
                    "url": self.base_urls["auth"],
                    "description": "User authentication and JWT token management",
                    "endpoints": ["/signup", "/login", "/token/refresh", "/token/revoke", "/health"]
                },
                "did-service": {
                    "url": self.base_urls["did"],
                    "description": "Decentralized Identifier (DID) creation and resolution",
                    "endpoints": ["/dids", "/dids/{did}", "/health"]
                },
                "credential-service": {
                    "url": self.base_urls["credential"],
                    "description": "Verifiable credential issuance",
                    "endpoints": ["/credentials/issue", "/health"]
                },
                "verification-service": {
                    "url": self.base_urls["verification"],
                    "description": "Credential verification and validation",
                    "endpoints": ["/credentials/verify", "/health"]
                }
            }
        } 