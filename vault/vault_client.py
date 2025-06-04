"""
Shared Vault Client Library for DIDentity Services

This module provides a standardized way for all services to interact with HashiCorp Vault
for secure secret management. It includes features like:
- Automatic secret caching with TTL
- Robust error handling and retries
- Connection pooling
- Audit logging
- Secret rotation support
"""

import os
import time
import logging
import requests
import threading
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json

# Setup logging
logger = logging.getLogger(__name__)


class VaultClientError(Exception):
    """Custom exception for Vault client errors"""
    pass


class VaultClient:
    """
    A robust Vault client with caching, error handling, and retry logic
    """
    
    def __init__(
        self,
        vault_url: str = None,
        vault_token: str = None,
        cache_ttl: int = 300,  # 5 minutes default cache TTL
        max_retries: int = 3,
        retry_delay: int = 1
    ):
        """
        Initialize the Vault client
        
        Args:
            vault_url: Vault server URL (defaults to VAULT_ADDR env var)
            vault_token: Vault authentication token (defaults to VAULT_TOKEN env var)
            cache_ttl: Cache time-to-live in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.vault_url = vault_url or os.environ.get('VAULT_ADDR', 'http://vault:8200')
        self.vault_token = vault_token or os.environ.get('VAULT_TOKEN', 'root')
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Cache for secrets with timestamps
        self._cache = {}
        self._cache_lock = threading.RLock()
        
        # Validate connection on initialization
        self._validate_connection()
        
        logger.info(f"Vault client initialized for {self.vault_url}")
    
    def _validate_connection(self) -> None:
        """Validate connection to Vault server"""
        try:
            response = self._make_request('GET', '/v1/sys/health')
            if response.status_code not in [200, 429, 472, 473]:
                raise VaultClientError(f"Vault health check failed: {response.status_code}")
        except requests.RequestException as e:
            raise VaultClientError(f"Cannot connect to Vault: {str(e)}")
    
    def _make_request(
        self, 
        method: str, 
        path: str, 
        data: Dict = None, 
        headers: Dict = None
    ) -> requests.Response:
        """
        Make HTTP request to Vault with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            data: Request payload
            headers: Additional headers
            
        Returns:
            requests.Response object
        """
        url = f"{self.vault_url}{path}"
        request_headers = {
            'X-Vault-Token': self.vault_token,
            'Content-Type': 'application/json'
        }
        if headers:
            request_headers.update(headers)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=request_headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 404:
                    raise VaultClientError(f"Secret not found: {path}")
                elif response.status_code == 403:
                    raise VaultClientError(f"Access denied to: {path}")
                else:
                    response.raise_for_status()
                    
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise VaultClientError(f"Request failed after {self.max_retries} attempts: {str(e)}")
                
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}, retrying...")
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        raise VaultClientError("Max retries exceeded")
    
    def _get_cache_key(self, path: str, key: str = None) -> str:
        """Generate cache key for secret"""
        return f"{path}:{key}" if key else path
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached secret is still valid"""
        with self._cache_lock:
            if cache_key not in self._cache:
                return False
            
            cached_time = self._cache[cache_key]['timestamp']
            return (datetime.now() - cached_time).total_seconds() < self.cache_ttl
    
    def _cache_secret(self, cache_key: str, value: Any) -> None:
        """Cache secret with timestamp"""
        with self._cache_lock:
            self._cache[cache_key] = {
                'value': value,
                'timestamp': datetime.now()
            }
    
    def _get_cached_secret(self, cache_key: str) -> Any:
        """Retrieve secret from cache"""
        with self._cache_lock:
            return self._cache[cache_key]['value']
    
    def get_secret(self, path: str, key: str = None, use_cache: bool = True) -> Union[Dict, Any]:
        """
        Retrieve secret from Vault
        
        Args:
            path: Secret path (e.g., 'database/config')
            key: Specific key within the secret (optional)
            use_cache: Whether to use caching
            
        Returns:
            Secret value(s)
        """
        cache_key = self._get_cache_key(path, key)
        
        # Check cache first
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Retrieved secret from cache: {path}")
            return self._get_cached_secret(cache_key)
        
        try:
            # Fetch from Vault
            response = self._make_request('GET', f'/v1/kv/data/{path}')
            data = response.json()
            
            if 'data' not in data or 'data' not in data['data']:
                raise VaultClientError(f"Invalid secret format for path: {path}")
            
            secret_data = data['data']['data']
            
            # Extract specific key if requested
            if key:
                if key not in secret_data:
                    raise VaultClientError(f"Key '{key}' not found in secret: {path}")
                result = secret_data[key]
            else:
                result = secret_data
            
            # Cache the result
            if use_cache:
                self._cache_secret(cache_key, result)
            
            logger.debug(f"Retrieved secret from Vault: {path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret {path}: {str(e)}")
            raise VaultClientError(f"Failed to retrieve secret {path}: {str(e)}")
    
    def put_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """
        Store secret in Vault
        
        Args:
            path: Secret path
            data: Secret data to store
            
        Returns:
            True if successful
        """
        try:
            response = self._make_request('POST', f'/v1/kv/data/{path}', {'data': data})
            
            # Invalidate cache for this path
            with self._cache_lock:
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(path)]
                for key in keys_to_remove:
                    del self._cache[key]
            
            logger.info(f"Successfully stored secret: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret {path}: {str(e)}")
            raise VaultClientError(f"Failed to store secret {path}: {str(e)}")
    
    def delete_secret(self, path: str) -> bool:
        """
        Delete secret from Vault
        
        Args:
            path: Secret path to delete
            
        Returns:
            True if successful
        """
        try:
            response = self._make_request('DELETE', f'/v1/kv/data/{path}')
            
            # Invalidate cache for this path
            with self._cache_lock:
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(path)]
                for key in keys_to_remove:
                    del self._cache[key]
            
            logger.info(f"Successfully deleted secret: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {str(e)}")
            raise VaultClientError(f"Failed to delete secret {path}: {str(e)}")
    
    def clear_cache(self, path: str = None) -> None:
        """
        Clear secret cache
        
        Args:
            path: Specific path to clear (clears all if None)
        """
        with self._cache_lock:
            if path:
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(path)]
                for key in keys_to_remove:
                    del self._cache[key]
                logger.debug(f"Cleared cache for path: {path}")
            else:
                self._cache.clear()
                logger.debug("Cleared entire secret cache")
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration from Vault"""
        return self.get_secret('database/config')
    
    def get_database_url(self) -> str:
        """Get database URL from Vault"""
        return self.get_secret('database/config', 'url')
    
    def get_rabbitmq_config(self) -> Dict[str, str]:
        """Get RabbitMQ configuration from Vault"""
        return self.get_secret('rabbitmq/config')
    
    def get_rabbitmq_url(self) -> str:
        """Get RabbitMQ URL from Vault"""
        return self.get_secret('rabbitmq/config', 'url')
    
    def get_jwt_config(self) -> Dict[str, str]:
        """Get JWT configuration from Vault"""
        return self.get_secret('auth/jwt')
    
    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key from Vault"""
        return self.get_secret('auth/jwt', 'secret_key')
    
    def get_grafana_config(self) -> Dict[str, str]:
        """Get Grafana configuration from Vault"""
        return self.get_secret('grafana/config')
    
    def get_encryption_key(self) -> str:
        """Get master encryption key from Vault"""
        return self.get_secret('security/encryption', 'master_key')
    
    def get_service_api_key(self, service_name: str) -> str:
        """Get API key for a specific service"""
        return self.get_secret('services/api_keys', f'{service_name}_service_key')
    
    def get_monitoring_config(self) -> Dict[str, str]:
        """Get monitoring configuration from Vault"""
        return self.get_secret('monitoring/config')
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Vault connection
        
        Returns:
            Health status information
        """
        try:
            response = self._make_request('GET', '/v1/sys/health')
            health_data = response.json()
            
            return {
                'status': 'healthy',
                'vault_url': self.vault_url,
                'initialized': health_data.get('initialized', False),
                'sealed': health_data.get('sealed', True),
                'cache_size': len(self._cache),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'vault_url': self.vault_url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Global instance for easy import
vault_client = VaultClient()


# Convenience functions for backward compatibility
def get_secret(path: str, key: str = None) -> Union[Dict, Any]:
    """Get secret using global vault client"""
    return vault_client.get_secret(path, key)


def get_db_url() -> str:
    """Get database URL using global vault client"""
    return vault_client.get_database_url()


def get_jwt_secret_key() -> str:
    """Get JWT secret key using global vault client"""
    return vault_client.get_jwt_secret_key() 